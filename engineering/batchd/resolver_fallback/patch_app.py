import sys
from pathlib import Path
p=Path(sys.argv[1]); s=p.read_text(encoding="utf-8-sig")
old="""def resolve_canonical_package(pid, allow_cache=True):
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
"""
new="""def _direct_canonical_package_record(pid,destination):
    base=os.environ.get('TMNM_CANONICAL_BRIDGE','http://127.0.0.1:8765').rstrip('/')
    url=base+'/api/package/'+urllib.parse.quote(str(pid),safe='')+'?destination='+urllib.parse.quote(str(destination),safe='')
    try:
        with urllib.request.urlopen(url,timeout=15) as r:
            data=json.loads(r.read().decode('utf-8-sig'))
    except Exception as exc:
        if getattr(exc,'code',None)==404: return None
        raise BridgeError('CANONICAL_PACKAGE_DETAIL_READ_FAILED '+str(exc))
    if not isinstance(data,dict): raise BridgeError('CANONICAL_PACKAGE_DETAIL_INVALID')
    if str(data.get('package_id') or '')!=str(pid): raise BridgeError('CANONICAL_PACKAGE_DETAIL_ID_MISMATCH')
    return data

def resolve_canonical_package(pid, allow_cache=True):
    if allow_cache:
        cached=CACHE.get(pid)
        if cached is not None and cached.get('canonical_article_body_loaded'): return cached
    for destination in ('TMNM','POLITIC_AL'):
        try:
            today=BRIDGE.today(destination); records,conflicts=exact_records_by_package_id(today)
            raw=records.get(pid)
            if raw is None:
                raw=_direct_canonical_package_record(pid,destination)
                if raw is None: continue
            p,_,_=complete_canonical_package(raw,pid,destination,conflicts.get(pid))
            if not p.get('ok'):
                p=placeholder(pid,destination,'CANONICAL TODAY RECORD INCOMPLETE',p.get('missing_fields') or [])
            CACHE[pid]=p; return p
        except BridgeError: continue
    CACHE.pop(pid,None); return None
"""
if s.count(old)!=1: raise SystemExit("EXACT_RESOLVER_BLOCK_COUNT="+str(s.count(old)))
p.with_suffix(".py.batchd_pre_resolver_fallback.bak").write_text(s,encoding="utf-8")
p.write_text(s.replace(old,new),encoding="utf-8")
print("PATCH=PASS")
