import json, os, time, urllib.parse, urllib.request, sys
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from pathlib import Path
from .bridge import CanonicalBridge, BridgeError, package_ids, exact_records_by_package_id, normalize_read_model_record, sha256_bytes
from .owner_workflow import WorkflowStore, canonical_snapshot, sha_obj, existing_control_room_provider, LIVE_FACEBOOK_AUTHORITY, SERVER_SIDE_PUBLISH_REFERENCE, HO057_SCOPE

BUILD_ID='CANONICAL_OWNER_WORKFLOW_PUBLISH_V1_DURABLE_APPROVAL_V1'
MODE='OWNER WORKFLOW — OWNER-DIRECT PUBLISH ENABLED'
CANONICAL_SOURCE='EXISTING_CONTROL_ROOM_CANONICAL_TODAY_READ_MODEL_8765'
PORT=int(os.environ.get('TMNM_OWNER_PORT','8766'))
UI_CACHE_BUST='TMNM-B7-UI-CACHE-01'
BRIDGE=CanonicalBridge(os.environ.get('TMNM_CANONICAL_BRIDGE','http://127.0.0.1:8765'))
ROOT=Path(__file__).resolve().parent
# TMNM_HO114_WORKFLOW_DIAGNOSTIC
HO114_DIAG_LOG=ROOT.parent/'evidence'/'HO114_WORKFLOW_DIAG.jsonl'
def _ho114_diag(method,path,package_id,status,label):
    if path not in {'/api/workflow/approve','/api/workflow/publish','/api/workflow/publish-now'}: return
    rec={'timestamp':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),
         'method':str(method or ''),'path':str(path or ''),
         'package_id':str(package_id or ''),'status':int(status),
         'workflow_result':str(label or '')}
    try:
        with HO114_DIAG_LOG.open('a',encoding='utf-8') as f:
            f.write(json.dumps(rec,separators=(',',':'))+'\n')
    except Exception:
        pass

START=time.time(); CACHE={}; LAST_SYNC=None; LAST_ERROR=None; WORKFLOW=WorkflowStore()

def placeholder(pid,destination,detail,missing=None):
    return {'package_id':pid,'source_drive_id':'','title':'','author':'','created_at':'',
      'workflow_status':'UNPROVEN','lifecycle':'CANONICAL DETAIL UNAVAILABLE','approval_status':'UNAVAILABLE',
      'destination':destination,
      'image':{'state':'CANONICAL_DETAIL_UNAVAILABLE','current_ref':'','source_drive_id':'','source_sha256':'','error':'CANONICAL_DETAIL_UNAVAILABLE'},
      'article_text':'','article_doc_id':'','canonical_detail_available':False,'detail_status':detail,
      'review_ready':False,'publish_enabled':False,'approve_enabled':False,'schedule_enabled':False,'edit_enabled':False,
      'owner_schedule_state':'UNSCHEDULED','fresh_owner_workflow':False,'missing_fields':missing or [],'_placeholder':True}

def _derive_package_readiness(p,pid,destination,conflict=None,require_article_body=True):
    """Derive readiness from canonical facts; pool candidates may rely on a persisted article reference."""
    image=p.get('image') if isinstance(p.get('image'),dict) else {}
    prod=str(p.get('workflow_status') or '').upper()
    rm=[]
    if str(p.get('package_id') or '')!=str(pid or ''): rm.append('package_id')
    if str(p.get('destination') or '')!=str(destination or ''): rm.append('destination')
    if prod not in {'READY','READY_FOR_REVIEW'}: rm.append('workflow_status')
    if not str(p.get('title') or '').strip(): rm.append('title')
    if not str(p.get('author') or '').strip(): rm.append('author')
    body_loaded=bool(str(p.get('article_text') or '').strip())
    article_ref=bool(str(p.get('article_doc_id') or '').strip())
    if require_article_body:
        if not body_loaded: rm.append('canonical_article_body')
    elif not (body_loaded or article_ref):
        rm.append('canonical_article_reference')
    if not str(image.get('source_drive_id') or '').strip(): rm.append('canonical_image_drive_id')
    if not str(image.get('source_sha256') or '').strip(): rm.append('canonical_image_sha256')
    if not p.get('ok'): rm.append('canonical_normalization')
    if conflict: rm.append('canonical_identity_conflict')
    return list(dict.fromkeys(rm))

def _hydrate_article_body_from_canonical_package(pid,destination):
    """Fallback to the existing 8765 canonical package read endpoint for the selected package body."""
    base=os.environ.get('TMNM_CANONICAL_BRIDGE','http://127.0.0.1:8765').rstrip('/')
    url=base+'/api/package/'+urllib.parse.quote(str(pid),safe='')+'?destination='+urllib.parse.quote(str(destination),safe='')
    try:
        with urllib.request.urlopen(url,timeout=15) as r:
            data=json.loads(r.read().decode('utf-8-sig'))
    except Exception as exc:
        raise BridgeError('CANONICAL_PACKAGE_ARTICLE_READ_FAILED '+str(exc))
    body=str(data.get('article_text') or '').strip() if isinstance(data,dict) else ''
    if not body:
        raise BridgeError('CANONICAL_PACKAGE_ARTICLE_BODY_EMPTY')
    return body

def complete_canonical_package(raw,pid,destination,conflict=None):
    """Normalize and fully hydrate one package for detail/publish validation."""
    p=normalize_read_model_record(raw,pid,destination,conflict)
    original_missing=list(dict.fromkeys(p.get('missing_fields') or []))
    p['missing_fields']=original_missing
    attempted=False; hydrated=False
    if not str(p.get('article_text') or '').strip() and p.get('article_doc_id'):
        attempted=True
        try:
            article=BRIDGE.article_document(p['article_doc_id'])
            if not str(article or '').strip(): raise BridgeError('CANONICAL_ARTICLE_DOCUMENT_EMPTY')
        except BridgeError as exc:
            try: article=_hydrate_article_body_from_canonical_package(pid,destination)
            except BridgeError as fallback_exc:
                article=''; p['hydration_error']=(str(exc)+' | '+str(fallback_exc))[:160]
        p['article_text']=str(article or '').strip(); hydrated=bool(p['article_text'])
    p['article_text']=str(p.get('article_text') or '').strip()
    p['canonical_article_body_loaded']=bool(p['article_text'])
    p['readiness_missing_fields']=_derive_package_readiness(p,pid,destination,conflict,True)
    p['missing_fields']=list(dict.fromkeys(original_missing+[x for x in p['readiness_missing_fields'] if x in {
        'package_id','destination','title','author','canonical_article_body',
        'canonical_image_drive_id','canonical_image_sha256','canonical_normalization',
        'canonical_identity_conflict'}]))
    p['review_ready']=not bool(p['readiness_missing_fields'])
    p['pool_action_candidate']=p['review_ready']
    return p,attempted,hydrated

def metadata_canonical_package(raw,pid,destination,conflict=None):
    """Normalize Article Pool metadata without article-document hydration."""
    p=normalize_read_model_record(raw,pid,destination,conflict)
    p['article_text']=str(p.get('article_text') or '').strip()
    p['canonical_article_body_loaded']=bool(p['article_text'])
    missing=_derive_package_readiness(p,pid,destination,conflict,False)
    p['pool_candidate_missing_fields']=missing
    p['pool_action_candidate']=not bool(missing)
    # Full review/publish readiness is deliberately not asserted by the list path.
    p['review_ready']=False
    p['publish_enabled']=False
    return p

def inventory_destination(destination):
    global LAST_SYNC,LAST_ERROR
    lifecycle=BRIDGE.lifecycle(destination); ids=package_ids(lifecycle)
    today=BRIDGE.today(destination); records,conflicts=exact_records_by_package_id(today)
    items=[]; readable=0; candidates=0; unavailable=0; not_candidates=0
    for pid in ids:
        raw=records.get(pid)
        if raw is None:
            p=placeholder(pid,destination,'CANONICAL TODAY RECORD UNAVAILABLE',['canonical_today_record']); unavailable+=1
        else:
            p=metadata_canonical_package(raw,pid,destination,conflicts.get(pid))
            if not p.get('ok'):
                p=placeholder(pid,destination,'CANONICAL TODAY RECORD INCOMPLETE',p.get('missing_fields') or []); unavailable+=1
            else:
                readable+=1
                if p.get('pool_action_candidate'): candidates+=1
                else: not_candidates+=1
        CACHE[pid]=p; items.append(p)
    LAST_SYNC=time.time(); LAST_ERROR=None
    return items,{'TOTAL_CANONICAL_IDS':len(ids),'READABLE_PACKAGES':readable,'READY_FOR_REVIEW':candidates,
      'NOT_REVIEW_READY':not_candidates,'CANONICAL_DETAIL_UNAVAILABLE':unavailable,
      'HYDRATION_SUCCESS_COUNT':0,'HYDRATION_FAILURE_COUNT':0,
      'ARTICLE_DOCUMENT_CALLS':0,'ACTIONABLE_READY_FOR_REVIEW_COUNT':candidates}

def resolve_canonical_package(pid, allow_cache=True):
    if allow_cache:
        cached=CACHE.get(pid)
        if cached is not None and cached.get('canonical_article_body_loaded'): return cached
    for destination in ('TMNM','POLITIC_AL'):
        try:
            today=BRIDGE.today(destination); records,conflicts=exact_records_by_package_id(today)
            raw=records.get(pid)
            if raw is None: continue
            p,_,_=complete_canonical_package(raw,pid,destination,conflicts.get(pid))
            if not p.get('ok'):
                p=placeholder(pid,destination,'CANONICAL TODAY RECORD INCOMPLETE',p.get('missing_fields') or [])
            CACHE[pid]=p; return p
        except BridgeError: continue
    CACHE.pop(pid,None); return None

def public(p): return {k:v for k,v in p.items() if not k.startswith('_')}

def health():
    try:
        lifecycle=BRIDGE.lifecycle('TMNM'); count=len(package_ids(lifecycle)); bridge='HEALTHY'; err=None
    except Exception as e:
        bridge='DEGRADED'; err=str(e); count=0
    return {'status':'HEALTHY' if bridge=='HEALTHY' else 'DEGRADED','build_id':BUILD_ID,'ui_build':BUILD_ID,
      'mode':MODE,'canonical_source':CANONICAL_SOURCE,'canonical_bridge':bridge,'sync_error':err,
      'queue_count_tmnm':count,'provider_mode':'OWNER_DIRECT_SINGLE_ATTEMPT','publish_route_mode':'ENABLED_OWNER_DIRECT',
      'scheduler_mode':'DISABLED','facebook_meta_calls_enabled':bool(LIVE_FACEBOOK_AUTHORITY),'uptime_seconds':int(time.time()-START)}

class H(BaseHTTPRequestHandler):
    def sendj(self,obj,code=200):
        b=json.dumps(obj,ensure_ascii=False).encode()
        self.send_response(code); self.send_header('Content-Type','application/json; charset=utf-8')
        self.send_header('Content-Length',str(len(b))); self.send_header('Cache-Control','no-store')
        self.end_headers(); self.wfile.write(b)
    def do_GET(self):
        u=urllib.parse.urlparse(self.path)
        if u.path=='/api/health': return self.sendj(health())
        if u.path.startswith('/api/approval-state/'):
            aid=urllib.parse.unquote(u.path[len('/api/approval-state/'):])
            state=WORKFLOW.approval_state(aid)
            return self.sendj({'schema':'TMNM_APPROVAL_V1','approval':state},200) if state else self.sendj({'error':'APPROVAL_NOT_FOUND'},404)
        if u.path=='/api/runtime': return self.sendj({'build_id':BUILD_ID,'mode':MODE,'process_id':os.getpid(),
            'executable_name':Path(sys.executable).name,'module':'tmnm_owner_console.app',
            'installed_root':str(ROOT.parent).replace(os.environ.get('LOCALAPPDATA',''),'%LOCALAPPDATA%') if os.environ.get('LOCALAPPDATA') else str(ROOT.parent),
            'canonical_source':CANONICAL_SOURCE,'publish_route_mode':'ENABLED_OWNER_DIRECT' if LIVE_FACEBOOK_AUTHORITY else 'DISABLED'})
        if u.path=='/api/packages':
            qs=urllib.parse.parse_qs(u.query); tab=qs.get('tab',['tmnm'])[0]
            author=qs.get('author',[''])[0]; q=qs.get('q',[''])[0].lower().strip()
            destination='POLITIC_AL' if tab=='politic-al' else 'TMNM'
            try: items,counters=inventory_destination(destination)
            except Exception as e: return self.sendj({'error':'CANONICAL_SYNC_FAILED','reason':str(e)},503)
            authors=sorted({p['author'] for p in items if p.get('canonical_detail_available') and p.get('author')})
            if author: items=[p for p in items if p.get('author')==author]
            if q: items=[p for p in items if q in ((p.get('title') or '')+' '+(p.get('author') or '')+' '+p['package_id']).lower()]
            return self.sendj({'items':[public(p) for p in items],'count':counters['TOTAL_CANONICAL_IDS'],
              'authors':authors,'counters':counters,'build_id':BUILD_ID,'mode':MODE})
        if u.path.startswith('/api/packages/') or u.path.startswith('/api/package/'):
            pid=urllib.parse.unquote(u.path.rsplit('/',1)[-1]); p=resolve_canonical_package(pid,allow_cache=True)
            if p and p.get('_placeholder'):
                return self.sendj({'error':'CANONICAL_DETAIL_UNAVAILABLE','package_id':pid,
                    'detail_status':p.get('detail_status'),'missing_fields':p.get('missing_fields',[]),'write_actions':'DISABLED'},409)
            return self.sendj(public(p),200) if p else self.sendj({'error':'PACKAGE_NOT_FOUND_IN_CURRENT_CANONICAL_VIEW'},404)
        if u.path.startswith('/api/image/'):
            did=urllib.parse.unquote(u.path[len('/api/image/'):]); expected=''
            for p in CACHE.values():
                if p.get('image',{}).get('source_drive_id')==did:
                    expected=p['image'].get('source_sha256',''); break
            if not any(p.get('image',{}).get('source_drive_id')==did for p in CACHE.values()):
                return self.sendj({'error':'IMAGE_NOT_REFERENCED_BY_CURRENT_CANONICAL_PACKAGE'},404)
            try: b,ctype=BRIDGE.media(did)
            except BridgeError as e: return self.sendj({'error':str(e)},404)
            actual=sha256_bytes(b)
            if expected and actual!=expected: return self.sendj({'error':'CANONICAL_IMAGE_SHA_MISMATCH'},409)
            self.send_response(200); self.send_header('Content-Type',ctype); self.send_header('Content-Length',str(len(b)))
            self.send_header('X-TMNM-Image-Drive-ID',did); self.send_header('X-TMNM-Image-SHA256',actual)
            self.send_header('Cache-Control','no-store'); self.end_headers(); self.wfile.write(b); return
        if u.path in ('/','/index.html'): return self.static('index.html','text/html; charset=utf-8')
        if u.path.startswith('/static/'):
            n=u.path.split('/')[-1]; return self.static(n,'text/css; charset=utf-8' if n.endswith('.css') else 'application/javascript; charset=utf-8')
        return self.sendj({'error':'NOT_FOUND'},404)
    def read_json(self,limit=1048576):
        try:
            n=int(self.headers.get('Content-Length','0') or 0)
            if n<0 or n>limit: raise ValueError('REQUEST_TOO_LARGE')
            return json.loads(self.rfile.read(n).decode('utf-8')) if n else {}
        except Exception:
            raise ValueError('INVALID_JSON')

    def do_POST(self):
        u=urllib.parse.urlparse(self.path)
        try:
            body=self.read_json()
        except ValueError as e:
            return self.sendj({'error':str(e)},400)

        if u.path=='/api/workflow/edit':
            pid=str(body.get('package_id') or '')
            p=CACHE.get(pid)
            if not p:return self.sendj({'error':'PACKAGE_NOT_IN_CURRENT_VIEW'},404)
            try:
                rec=WORKFLOW.edit(p,body.get('edit') or {})
            except ValueError as e:return self.sendj({'error':str(e)},409)
            return self.sendj({'status':'EDIT_STAGED','package_id':pid,'payload':rec['payload'],
                'payload_sha256':rec['payload_sha256'],'canonical_snapshot_sha256':rec['canonical_snapshot_sha256'],
                'storage':'EPHEMERAL_OWNER_WORKFLOW_MEMORY','canonical_upstream_mutated':False})

        if u.path=='/api/workflow/payload':
            pid=str(body.get('package_id') or '')
            p=CACHE.get(pid)
            if not p:return self.sendj({'error':'PACKAGE_NOT_IN_CURRENT_VIEW'},404)
            try:
                from .owner_workflow import validate_actionable
                snap=canonical_snapshot(p); ok,reason=validate_actionable(snap)
                if not ok:return self.sendj({'error':reason},409)
                payload,payload_sha=WORKFLOW.payload_for(p)
            except ValueError as e:return self.sendj({'error':str(e)},409)
            return self.sendj({'status':'PAYLOAD_READY','package_id':pid,'payload':payload,
                'payload_sha256':payload_sha,'canonical_snapshot_sha256':sha_obj(snap)})

        if u.path=='/api/workflow/approve':
            pid=str(body.get('package_id') or '')
            if self.headers.get('X-TMNM-Owner-Intent')!='APPROVE':
                _ho114_diag('POST',u.path,pid,409,'EXPLICIT_OWNER_APPROVAL_REQUIRED')
                return self.sendj({'error':'EXPLICIT_OWNER_APPROVAL_REQUIRED'},409)
            p=resolve_canonical_package(pid,allow_cache=False)
            if not p:
                _ho114_diag('POST',u.path,pid,404,'PACKAGE_NOT_FOUND_IN_CURRENT_CANONICAL_VIEW')
                return self.sendj({'error':'PACKAGE_NOT_FOUND_IN_CURRENT_CANONICAL_VIEW'},404)
            if p.get('_placeholder'):
                _ho114_diag('POST',u.path,pid,409,'CANONICAL_DETAIL_UNAVAILABLE')
                return self.sendj({'error':'CANONICAL_DETAIL_UNAVAILABLE','write_actions':'DISABLED'},409)
            try:
                a=WORKFLOW.approve(p,str(body.get('payload_sha256') or ''))
            except ValueError as e:
                _ho114_diag('POST',u.path,pid,409,str(e))
                return self.sendj({'error':str(e)},409)
            _ho114_diag('POST',u.path,pid,200,'OWNER_APPROVED')
            return self.sendj({'status':'OWNER_APPROVED','approval_id':a['approval_id'],
                'package_id':a['package_id'],'destination':a['destination'],
                'payload_sha256':a['payload_sha256'],'canonical_snapshot_sha256':a['canonical_snapshot_sha256'],
                'expires_at':a['expires_at'],'approval_storage':'TMNM_APPROVAL_V1_DURABLE','publish_authority':('DURABLE_EPOCH03_BOUND' if WORKFLOW.epoch03_bound_approval(a['approval_id']) else 'ZERO')})

        if u.path=='/api/workflow/publish-now':
            pid=str(body.get('package_id') or '')
            if self.headers.get('X-TMNM-Owner-Intent')!='PUBLISH_NOW':
                _ho114_diag('POST',u.path,pid,409,'EXPLICIT_OWNER_PUBLISH_NOW_INTENT_REQUIRED')
                return self.sendj({'error':'EXPLICIT_OWNER_PUBLISH_NOW_INTENT_REQUIRED','retry':False},409)
            p=resolve_canonical_package(pid,allow_cache=False)
            if not p:
                _ho114_diag('POST',u.path,pid,404,'PACKAGE_NOT_FOUND_IN_CURRENT_CANONICAL_VIEW')
                return self.sendj({'error':'PACKAGE_NOT_FOUND_IN_CURRENT_CANONICAL_VIEW','retry':False},404)
            if p.get('_placeholder'):
                _ho114_diag('POST',u.path,pid,409,'CANONICAL_DETAIL_UNAVAILABLE')
                return self.sendj({'error':'CANONICAL_DETAIL_UNAVAILABLE','write_actions':'DISABLED','retry':False},409)
            try:
                action_id,binding,payload=WORKFLOW.prepare_publish_now(p,self.headers.get('X-TMNM-Owner-Intent'))
                result=WORKFLOW.invoke_publish_now_once(action_id,binding,payload,existing_control_room_provider)
            except ValueError as e:
                _ho114_diag('POST',u.path,pid,409,str(e))
                return self.sendj({'error':str(e),'retry':False},409)
            code=423 if result.get('status')=='BLOCKED' else 200
            _ho114_diag('POST',u.path,pid,code,result.get('status') or 'PUBLISH_RESULT')
            return self.sendj({'status':'PUBLISH_NOW_RESULT','action_id':action_id,'result':result,
                'provider_reference':SERVER_SIDE_PUBLISH_REFERENCE['name'],
                'facebook_publish_authority':('GENERIC_DURABLE_ONE_SHOT' if binding.get('authority_scope')=='TMNM-GENERIC-OWNER-PUBLISH-NOW-V1' else 'ZERO'),
                'retry':False},code)

        if u.path=='/api/workflow/publish':
            pid=str(body.get('package_id') or '')
            p=resolve_canonical_package(pid,allow_cache=False)
            if not p:
                _ho114_diag('POST',u.path,pid,404,'PACKAGE_NOT_FOUND_IN_CURRENT_CANONICAL_VIEW')
                return self.sendj({'error':'PACKAGE_NOT_FOUND_IN_CURRENT_CANONICAL_VIEW'},404)
            if p.get('_placeholder'):
                _ho114_diag('POST',u.path,pid,409,'CANONICAL_DETAIL_UNAVAILABLE')
                return self.sendj({'error':'CANONICAL_DETAIL_UNAVAILABLE','write_actions':'DISABLED','retry':False},409)
            try:
                action_id,binding,payload=WORKFLOW.prepare_publish(
                    p,str(body.get('approval_id') or ''),str(body.get('payload_sha256') or ''),
                    self.headers.get('X-TMNM-Owner-Intent'))
                result=WORKFLOW.invoke_once(action_id,binding,payload,existing_control_room_provider)
            except ValueError as e:
                _ho114_diag('POST',u.path,pid,409,str(e))
                return self.sendj({'error':str(e),'retry':False},409)
            # Explicit approved Publish Once may cross the existing server-side provider boundary.
            code=423 if result.get('status')=='BLOCKED' else 200
            _ho114_diag('POST',u.path,pid,code,result.get('status') or 'PUBLISH_RESULT')
            return self.sendj({'action_id':action_id,'binding':binding,'result':result,
                'provider_reference':SERVER_SIDE_PUBLISH_REFERENCE['name'],
                'facebook_publish_authority':('TRANSACTION_BOUND_HO057' if binding.get('authority_scope')==HO057_SCOPE else 'ZERO')},code)

        if u.path=='/api/publish-now' or 'publish' in u.path or 'schedule' in u.path:
            return self.sendj({'error':'WRITE_DISABLED_MASTER_HOLD','build_id':BUILD_ID,'mode':MODE},423)

        return self.sendj({'error':'NOT_FOUND'},404)

    def static(self,n,ctype):
        p=ROOT/'static'/n
        if not p.is_file(): return self.sendj({'error':'NOT_FOUND'},404)
        b=p.read_bytes()
        if n=='index.html':
            hits=b.count(b'/static/app.js')+b.count(b'"static/app.js')
            if hits!=1: return self.sendj({'error':'UI_CACHE_BUST_APP_JS_REFERENCE_NOT_EXACT'},500)
            if b'/static/app.js' in b:
                b=b.replace(b'/static/app.js',('/static/app.js?v='+UI_CACHE_BUST).encode('ascii'),1)
            else:
                b=b.replace(b'"static/app.js',('static/app.js?v='+UI_CACHE_BUST).encode('ascii'),1)
        self.send_response(200); self.send_header('Content-Type',ctype)
        self.send_header('Cache-Control','no-store, no-cache, must-revalidate, max-age=0')
        self.send_header('Pragma','no-cache'); self.send_header('Expires','0')
        self.send_header('Content-Length',str(len(b))); self.end_headers(); self.wfile.write(b)
    def log_message(self,*a): pass

def main(): ThreadingHTTPServer(('127.0.0.1',PORT),H).serve_forever()
if __name__=='__main__': main()
