"""MASTER366 credential-safe Meta READ-ONLY verification layer.

This module deliberately contains no POST/PUT/PATCH/DELETE implementation.
Credentials are accepted only in process memory by a caller; never CLI args.
"""
from __future__ import annotations
import json,ssl,urllib.parse,urllib.request,urllib.error
from dataclasses import dataclass
GRAPH_HOST="graph.facebook.com"
API_VERSION="v26.0"
ALLOWED_FIELDS={"id","name","tasks","message","created_time","permalink_url"}
class MetaReadOnlyError(RuntimeError): pass
def _safe_error(exc):
    code=getattr(exc,"code",None)
    return {"kind":"HTTP_ERROR" if code else "NETWORK_ERROR","http_status":code}
@dataclass
class ReadOnlyMeta:
    token:str
    timeout:float=15.0
    def __post_init__(self):
        if not self.token or len(self.token)<8: raise MetaReadOnlyError("CREDENTIAL_REQUIRED")
    def get(self,path,fields):
        if not path.startswith("/") or ".." in path: raise MetaReadOnlyError("BAD_PATH")
        wanted=list(fields)
        if not wanted or any(x not in ALLOWED_FIELDS for x in wanted): raise MetaReadOnlyError("FIELD_NOT_ALLOWED")
        query=urllib.parse.urlencode({"fields":",".join(wanted)})
        url=f"https://{GRAPH_HOST}/{API_VERSION}{path}?{query}"
        req=urllib.request.Request(url,headers={"Authorization":"Bearer "+self.token,"User-Agent":"TMNM-MASTER366-READONLY"},method="GET")
        if req.get_method()!="GET": raise MetaReadOnlyError("READ_ONLY_VIOLATION")
        try:
            with urllib.request.urlopen(req,timeout=self.timeout,context=ssl.create_default_context()) as res:
                body=res.read(2_000_000)
        except Exception as exc:
            raise MetaReadOnlyError(json.dumps(_safe_error(exc),sort_keys=True)) from None
        try: return json.loads(body)
        except Exception: raise MetaReadOnlyError("INVALID_JSON") from None
    def page_identity(self,page_id):
        return self.get("/"+str(page_id),["id","name","tasks"])
    def post_by_id(self,post_id):
        return self.get("/"+str(post_id),["id","message","created_time","permalink_url"])
