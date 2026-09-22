import json,os,sys,tempfile,threading
from pathlib import Path
ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT))
from tmnm_fb_publisher import Store,Publisher,control_room_publish
class Writer:
 def __init__(self,mode='success'): self.mode=mode; self.calls=[]; self.lock=threading.Lock()
 def publish(self,**kw):
  with self.lock: self.calls.append(kw)
  if self.mode=='fail': return {'kind':'definite_failure','error':'access_token=TOPSECRET Bearer SECONDSECRET'}
  return {'kind':'success','post_id':'mock_post_1'}
def payload(g='g1'): return {'article_guid':g,'approved':True,'destination_page_id':'mock_page','message':'hello'}
def check(cond,msg):
 if not cond: raise AssertionError(msg)
def main():
 base=Path(os.environ.get('TMNM_WIN_TEST_ROOT',tempfile.mkdtemp(prefix='TMNM Master365 With Spaces '))); base.mkdir(parents=True,exist_ok=True)
 db=base/'State With Spaces'/'publisher state.sqlite3'
 # restart persistence
 w=Writer(); p=Publisher(Store(db),w); r=p.publish(payload()); check(r.state=='PUBLISHED','publish'); p2=Publisher(Store(db),w); p2.publish(payload()); check(len(w.calls)==1,'restart duplicate')
 # concurrency
 db2=base/'Concurrent Space'/'state.sqlite3'; w2=Writer(); outs=[]
 def go(): outs.append(Publisher(Store(db2),w2).publish(payload('same-guid')).state)
 ts=[threading.Thread(target=go) for _ in range(20)]
 [t.start() for t in ts]; [t.join() for t in ts]; check(len(w2.calls)==1,'concurrent duplicate')
 # retry auth persistence/consumption
 db3=base/'Retry Space'/'state.sqlite3'; wf=Writer('fail'); s=Store(db3); Publisher(s,wf).publish(payload('retry-guid')); Publisher(Store(db3),wf).publish(payload('retry-guid')); check(len(wf.calls)==1,'failed definite repeated')
 Store(db3).authorize_retry('retry-guid','operator-test','explicit retry')
 auth=Store(db3).retry_authorization('retry-guid'); check(auth and auth['consumed_at'] is None,'auth persistence')
 Publisher(Store(db3),wf).publish(payload('retry-guid')); check(len(wf.calls)==2,'one authorized retry')
 check(Store(db3).retry_authorization('retry-guid')['consumed_at'] is not None,'auth consumed')
 Publisher(Store(db3),wf).publish(payload('retry-guid')); check(len(wf.calls)==2,'consumed gate')
 # adapter deterministic + sanitizer
 rr=control_room_publish(Publisher(Store(base/'Adapter Space'/'s.sqlite3'),Writer()),payload('adapter-guid')); check(rr['state']=='PUBLISHED' and rr['ok'] is True,'adapter')
 secret_state=Store(db3).get('retry-guid'); blob=json.dumps(secret_state)+json.dumps(rr)
 check('TOPSECRET' not in blob and 'SECONDSECRET' not in blob,'secret leak')
 # static zero-network guard
 source=(ROOT/'tmnm_fb_publisher'/'core.py').read_text(encoding='utf-8')
 for banned in ('graph.facebook.com','requests.','urllib.request','http.client','published=false'): check(banned not in source,'network/meta string '+banned)
 result={'STATUS':'PASS','TESTS':['SQLITE_RESTART','CONCURRENT_GUID','RETRY_AUTH_PERSIST_CONSUME','PATHS_WITH_SPACES','CONTROL_ROOM_STRUCTURED','SECRET_FREE_RESULT','ZERO_META_TRAFFIC_STATIC'],'META_TRAFFIC':'ZERO','WRITE_TRANSPORT':'MOCK_ONLY'}
 out=Path(os.environ['TMNM_RESULT_PATH']); out.parent.mkdir(parents=True,exist_ok=True); out.write_text(json.dumps(result,sort_keys=True),encoding='utf-8')
 print(json.dumps(result,sort_keys=True))
if __name__=='__main__':
 try: main()
 except Exception as e:
  out=Path(os.environ.get('TMNM_RESULT_PATH','MASTER365_FAILURE.txt')); out.parent.mkdir(parents=True,exist_ok=True); out.write_text(json.dumps({'STATUS':'FAIL','ERROR':str(e)}),encoding='utf-8'); print(out.read_text()); raise
