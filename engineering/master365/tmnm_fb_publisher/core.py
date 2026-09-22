from __future__ import annotations
import hashlib,json,sqlite3,uuid
from dataclasses import dataclass
from datetime import datetime,timezone
from pathlib import Path
from typing import Protocol,Optional
BLOCKING={'PENDING','PUBLISHED','FAILED_DEFINITE','AMBIGUOUS','RECONCILING','RECONCILED_PUBLISHED','RECONCILED_NOT_FOUND','HOLD'}
def now(): return datetime.now(timezone.utc).isoformat()
def payload_hash(message): return hashlib.sha256(message.encode()).hexdigest()
class MetaWriteTransport(Protocol):
 def publish(self,*,page_id,message,attempt_id): ...
class MetaReadTransport(Protocol):
 def reconcile(self,*,page_id,message,attempt_id,attempted_at): ...
class AuditSink(Protocol):
 def write(self,receipt): ...
@dataclass(frozen=True)
class Result:
 state:str; article_guid:str; attempt_id:Optional[str]=None; post_id:Optional[str]=None; error:Optional[str]=None; audit_state:Optional[str]=None
 def as_dict(self): return {k:v for k,v in self.__dict__.items() if v is not None}
def sanitize(x):
 s=str(x or '')
 for marker in ('access_token=','Bearer '):
  if marker in s: s=s.split(marker)[0]+marker+'[REDACTED]'
 return s[:1000]
class Store:
 def __init__(self,path): self.path=str(path); self._init()
 def connect(self):
  c=sqlite3.connect(self.path,timeout=10,isolation_level=None); c.row_factory=sqlite3.Row; return c
 def _init(self):
  Path(self.path).parent.mkdir(parents=True,exist_ok=True)
  with self.connect() as c: c.executescript("""PRAGMA journal_mode=WAL;
CREATE TABLE IF NOT EXISTS publication(article_guid TEXT PRIMARY KEY,payload_sha256 TEXT NOT NULL,page_id TEXT NOT NULL,state TEXT NOT NULL,attempt_id TEXT,attempted_at TEXT,post_id TEXT,error TEXT,updated_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS audit_queue(attempt_id TEXT PRIMARY KEY,receipt_json TEXT NOT NULL,state TEXT NOT NULL DEFAULT 'PENDING',error TEXT);
CREATE TABLE IF NOT EXISTS retry_authorization(article_guid TEXT PRIMARY KEY,authorized_by TEXT NOT NULL,reason TEXT NOT NULL,authorized_at TEXT NOT NULL,consumed_at TEXT);""")
 def acquire(self,guid,h,page):
  c=self.connect()
  try:
   c.execute('BEGIN IMMEDIATE'); row=c.execute('SELECT * FROM publication WHERE article_guid=?',(guid,)).fetchone()
   if row and row['state']!='FAILED_DEFINITE' and row['state'] in BLOCKING: c.rollback(); return None,dict(row)
   if row and row['payload_sha256']!=h: c.rollback(); raise ValueError('PAYLOAD_HASH_MISMATCH')
   if row and row['state']=='FAILED_DEFINITE':
    auth=c.execute('SELECT * FROM retry_authorization WHERE article_guid=? AND consumed_at IS NULL',(guid,)).fetchone()
    if not auth: c.rollback(); return None,dict(row)
   aid=str(uuid.uuid4()); ts=now()
   if row and row['state']=='FAILED_DEFINITE':
    cur=c.execute('UPDATE retry_authorization SET consumed_at=? WHERE article_guid=? AND consumed_at IS NULL',(ts,guid))
    if cur.rowcount!=1: c.rollback(); return None,dict(row)
   c.execute("""INSERT INTO publication(article_guid,payload_sha256,page_id,state,attempt_id,attempted_at,updated_at) VALUES(?,?,?,?,?,?,?)
ON CONFLICT(article_guid) DO UPDATE SET state=excluded.state,attempt_id=excluded.attempt_id,attempted_at=excluded.attempted_at,error=NULL,updated_at=excluded.updated_at""",(guid,h,page,'PENDING',aid,ts,ts))
   c.commit(); return aid,None
  finally: c.close()
 def authorize_retry(self,guid,authorized_by,reason):
  if not authorized_by or not reason: raise ValueError('RETRY_AUTHORITY_REQUIRED')
  c=self.connect()
  try:
   c.execute('BEGIN IMMEDIATE'); row=c.execute('SELECT state FROM publication WHERE article_guid=?',(guid,)).fetchone()
   if not row or row['state']!='FAILED_DEFINITE': c.rollback(); raise ValueError('RETRY_NOT_ELIGIBLE')
   c.execute("""INSERT INTO retry_authorization(article_guid,authorized_by,reason,authorized_at,consumed_at) VALUES(?,?,?,?,NULL)
ON CONFLICT(article_guid) DO UPDATE SET authorized_by=excluded.authorized_by,reason=excluded.reason,authorized_at=excluded.authorized_at,consumed_at=NULL""",(guid,str(authorized_by),sanitize(reason),now())); c.commit()
  finally: c.close()
 def retry_authorization(self,guid):
  with self.connect() as c:
   r=c.execute('SELECT * FROM retry_authorization WHERE article_guid=?',(guid,)).fetchone(); return dict(r) if r else None
 def set(self,guid,state,post_id=None,error=None):
  with self.connect() as c: c.execute('UPDATE publication SET state=?,post_id=COALESCE(?,post_id),error=?,updated_at=? WHERE article_guid=?',(state,post_id,error,now(),guid))
 def get(self,guid):
  with self.connect() as c:
   r=c.execute('SELECT * FROM publication WHERE article_guid=?',(guid,)).fetchone(); return dict(r) if r else None
 def queue_audit(self,receipt):
  with self.connect() as c: c.execute('INSERT OR IGNORE INTO audit_queue(attempt_id,receipt_json) VALUES(?,?)',(receipt['attempt_id'],json.dumps(receipt,sort_keys=True)))
 def pending_audits(self):
  with self.connect() as c: return [dict(r) for r in c.execute("SELECT * FROM audit_queue WHERE state!='DONE'")]
 def audit_done(self,aid):
  with self.connect() as c: c.execute("UPDATE audit_queue SET state='DONE',error=NULL WHERE attempt_id=?",(aid,))
 def audit_fail(self,aid,e):
  with self.connect() as c: c.execute("UPDATE audit_queue SET state='FAILED',error=? WHERE attempt_id=?",(sanitize(e),aid))
class Publisher:
 def __init__(self,store,writer): self.store=store; self.writer=writer
 def publish(self,payload):
  guid=payload.get('article_guid'); page=payload.get('destination_page_id'); msg=payload.get('message')
  if payload.get('approved') is not True or not guid or not page or not isinstance(msg,str) or not msg.strip(): return Result('FAILED_DEFINITE',guid or '',error='VALIDATION_FAILED')
  try: aid,existing=self.store.acquire(guid,payload_hash(msg),page)
  except Exception as e: return Result('FAILED_DEFINITE',guid,error=sanitize(e))
  if not aid: return Result(existing['state'],guid,existing.get('attempt_id'),existing.get('post_id'),existing.get('error'))
  try: response=self.writer.publish(page_id=page,message=msg,attempt_id=aid)
  except Exception as e: self.store.set(guid,'AMBIGUOUS',error=sanitize(e)); return Result('AMBIGUOUS',guid,aid,error=sanitize(e))
  if response.get('kind')=='success' and response.get('post_id'):
   self.store.set(guid,'PUBLISHED',post_id=response['post_id']); self.store.queue_audit(self.receipt(guid)); return Result('PUBLISHED',guid,aid,response['post_id'],'','PENDING')
  if response.get('kind')=='definite_failure':
   err=sanitize(response.get('error','META_REJECTED')); self.store.set(guid,'FAILED_DEFINITE',error=err); return Result('FAILED_DEFINITE',guid,aid,error=err)
  self.store.set(guid,'AMBIGUOUS',error='UNVERIFIABLE_META_RESULT'); return Result('AMBIGUOUS',guid,aid,error='UNVERIFIABLE_META_RESULT')
 def receipt(self,guid):
  r=self.store.get(guid); return {k:r[k] for k in ('article_guid','payload_sha256','page_id','state','attempt_id','attempted_at','post_id','error','updated_at')}
class Reconciler:
 def __init__(self,store,reader): self.store=store; self.reader=reader
 def reconcile(self,guid):
  r=self.store.get(guid)
  if not r or r['state']!='AMBIGUOUS': return Result(r['state'] if r else 'FAILED_DEFINITE',guid,error='NOT_AMBIGUOUS')
  self.store.set(guid,'RECONCILING')
  try: out=self.reader.reconcile(page_id=r['page_id'],message='',attempt_id=r['attempt_id'],attempted_at=r['attempted_at'])
  except Exception as e: self.store.set(guid,'AMBIGUOUS',error=sanitize(e)); return Result('AMBIGUOUS',guid,r['attempt_id'],error=sanitize(e))
  if out.get('kind')=='found' and out.get('post_id'): self.store.set(guid,'RECONCILED_PUBLISHED',post_id=out['post_id']); return Result('RECONCILED_PUBLISHED',guid,r['attempt_id'],out['post_id'])
  if out.get('kind')=='not_found': self.store.set(guid,'RECONCILED_NOT_FOUND'); return Result('RECONCILED_NOT_FOUND',guid,r['attempt_id'])
  self.store.set(guid,'AMBIGUOUS',error='RECONCILIATION_INCONCLUSIVE'); return Result('AMBIGUOUS',guid,r['attempt_id'],error='RECONCILIATION_INCONCLUSIVE')
class AuditWorker:
 def __init__(self,store,sink): self.store=store; self.sink=sink
 def run_once(self):
  for row in self.store.pending_audits():
   try: self.sink.write(json.loads(row['receipt_json'])); self.store.audit_done(row['attempt_id'])
   except Exception as e: self.store.audit_fail(row['attempt_id'],e)
