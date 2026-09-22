"""TMNM 8766 Phase-2 Meta connection guard. NON-LIVE; no Facebook write endpoints."""
from __future__ import annotations
import os, secrets, urllib.parse
from dataclasses import dataclass

APP_ID="1754274758914441"
PAGE_ID="1021402681056527"
GRAPH_VERSION="v26.0"
REDIRECT_URI="http://localhost:8767/meta/callback"
AUTH_ENDPOINT=f"https://www.facebook.com/{GRAPH_VERSION}/dialog/oauth"
SCOPES=("pages_show_list","pages_read_engagement","pages_manage_posts")
CALLBACK_PATH="/meta/callback"

@dataclass(frozen=True)
class MetaPreflightResult:
    META_AUTH:str; TMNM_PAGE_ID_MATCH:str; REQUIRED_ACCESS:str; FACEBOOK_WRITE:int=0
    def as_dict(self): return self.__dict__.copy()

class OAuthGuard:
    def __init__(self): self._state=None
    def begin(self):
        self._state=secrets.token_urlsafe(32)
        q={"client_id":APP_ID,"redirect_uri":REDIRECT_URI,"state":self._state,
           "response_type":"code","scope":",".join(SCOPES)}
        return AUTH_ENDPOINT+"?"+urllib.parse.urlencode(q)
    def accept_callback(self,raw_target):
        """Validate callback and return authorization code only. Never returns/logs URL or tokens."""
        try: u=urllib.parse.urlsplit(raw_target)
        except Exception: raise ValueError("MALFORMED_CALLBACK")
        if u.path!=CALLBACK_PATH: raise ValueError("UNEXPECTED_CALLBACK_PATH")
        q=urllib.parse.parse_qs(u.query,keep_blank_values=True,strict_parsing=True)
        if self._state is None: raise ValueError("NO_PENDING_AUTH")
        if len(q.get("state",[]))!=1: raise ValueError("MISSING_STATE")
        if not secrets.compare_digest(q["state"][0],self._state):
            self._state=None; raise ValueError("STATE_MISMATCH")
        self._state=None
        if "error" in q: raise ValueError("AUTHORIZATION_DENIED")
        if len(q.get("code",[]))!=1 or not q["code"][0]: raise ValueError("MISSING_AUTHORIZATION_RESULT")
        if any(k not in {"state","code"} for k in q): raise ValueError("MALFORMED_CALLBACK")
        return q["code"][0]

class ProtectedTokenStore:
    """Windows DPAPI storage. Caller must never log the supplied/returned secret."""
    def __init__(self,path): self.path=path
    def save(self,token):
        if os.name!="nt": raise RuntimeError("WINDOWS_DPAPI_REQUIRED")
        import win32crypt
        blob=win32crypt.CryptProtectData(token.encode(),None,None,None,None,0)[1]
        os.makedirs(os.path.dirname(self.path),exist_ok=True)
        with open(self.path,"wb") as h:h.write(blob)
    def load(self):
        if os.name!="nt": raise RuntimeError("WINDOWS_DPAPI_REQUIRED")
        import win32crypt
        with open(self.path,"rb") as h:blob=h.read()
        return win32crypt.CryptUnprotectData(blob,None,None,None,0)[1].decode()

def read_only_preflight(user_token,graph_get):
    """graph_get is the sole network boundary and MUST implement GET only."""
    try: pages=graph_get("/me/accounts",{"fields":"name,access_token,tasks"},user_token)["data"]
    except Exception:return MetaPreflightResult("HOLD","HOLD","HOLD")
    page=next((p for p in pages if str(p.get("id"))==PAGE_ID),None)
    if not page:return MetaPreflightResult("PASS","HOLD","HOLD")
    tasks=set(page.get("tasks") or [])
    access="PASS" if ({"CREATE_CONTENT","PROFILE_PLUS_CREATE_CONTENT"} & tasks) else "HOLD"
    return MetaPreflightResult("PASS","PASS",access)
