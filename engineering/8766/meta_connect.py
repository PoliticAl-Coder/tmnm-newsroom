"""TMNM 8766 Phase-2 Meta connection. No Facebook write endpoints."""
from __future__ import annotations
import base64, hashlib, json, os, secrets, urllib.parse, urllib.request
from dataclasses import dataclass

APP_ID="1754274758914441"
PAGE_ID="1021402681056527"
GRAPH_VERSION="v26.0"
SCOPES=("pages_show_list","pages_read_engagement","pages_manage_posts")

@dataclass(frozen=True)
class MetaPreflightResult:
    META_AUTH:str; TMNM_PAGE_ID_MATCH:str; REQUIRED_ACCESS:str; FACEBOOK_WRITE:int=0
    def as_dict(self): return self.__dict__.copy()

class ProtectedTokenStore:
    """Windows DPAPI storage; raw tokens are never returned in evidence."""
    def __init__(self,path): self.path=path
    def save(self,token:str):
        if os.name!="nt": raise RuntimeError("WINDOWS_DPAPI_REQUIRED")
        import win32crypt
        blob=win32crypt.CryptProtectData(token.encode(),None,None,None,None,0)[1]
        os.makedirs(os.path.dirname(self.path),exist_ok=True)
        with open(self.path,"wb") as f:f.write(blob)
    def load(self)->str:
        if os.name!="nt": raise RuntimeError("WINDOWS_DPAPI_REQUIRED")
        import win32crypt
        with open(self.path,"rb") as f: blob=f.read()
        return win32crypt.CryptUnprotectData(blob,None,None,None,0)[1].decode()

def make_authorize_url(redirect_uri,state):
    q={"client_id":APP_ID,"redirect_uri":redirect_uri,"state":state,"response_type":"code","scope":",".join(SCOPES)}
    return "https://www.facebook.com/"+GRAPH_VERSION+"/dialog/oauth?"+urllib.parse.urlencode(q)

def new_state(): return secrets.token_urlsafe(32)

def read_only_preflight(user_token, graph_get):
    """GET-only. graph_get(path, params, token) must never perform writes."""
    try:
        pages=graph_get("/me/accounts",{"fields":"name,access_token,tasks"},user_token)["data"]
    except Exception:
        return MetaPreflightResult("HOLD","HOLD","HOLD")
    page=next((p for p in pages if str(p.get("id"))==PAGE_ID),None)
    if not page:return MetaPreflightResult("PASS","HOLD","HOLD")
    tasks=set(page.get("tasks") or [])
    # Current Meta Pages response exposes Page tasks; CREATE_CONTENT is required for posting.
    access="PASS" if ("CREATE_CONTENT" in tasks or "PROFILE_PLUS_CREATE_CONTENT" in tasks) else "HOLD"
    return MetaPreflightResult("PASS","PASS",access)
