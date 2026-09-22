"""TMNM 8766 Meta CONNECT client — /exec callback engineering proof. GET-only discovery; no Facebook write endpoints."""
from __future__ import annotations
import json, os, secrets, time, urllib.parse, urllib.request, webbrowser
from dataclasses import dataclass

APP_ID="1754274758914441"
PAGE_ID="1021402681056527"
GRAPH_VERSION="v26.0"
EXCHANGE_BASE="https://script.google.com/macros/s/AKfycbyyPnHf2HLe0rHs2U01QzxzUvsEiqBJ2DPV8Z1asX11AKqNjBtyfd844eVDYKyKNda1/exec"
META_REDIRECT_URI=EXCHANGE_BASE
AUTH_ENDPOINT=f"https://www.facebook.com/{GRAPH_VERSION}/dialog/oauth"
SCOPES=("pages_show_list","pages_read_engagement","pages_manage_posts")

@dataclass(frozen=True)
class MetaPreflightResult:
    META_AUTH:str; TMNM_PAGE_ID_MATCH:str; REQUIRED_ACCESS:str; FACEBOOK_WRITE:int=0
    def as_dict(self): return self.__dict__.copy()

class ProtectedTokenStore:
    def __init__(self,path): self.path=os.fspath(path)
    def save(self,token):
        if os.name!="nt": raise RuntimeError("WINDOWS_DPAPI_REQUIRED")
        import win32crypt
        blob=win32crypt.CryptProtectData(token.encode(),None,None,None,None,0)
        os.makedirs(os.path.dirname(self.path),exist_ok=True)
        with open(self.path,"wb") as h:h.write(blob)
    def load(self):
        if os.name!="nt": raise RuntimeError("WINDOWS_DPAPI_REQUIRED")
        import win32crypt
        with open(self.path,"rb") as h:blob=h.read()
        return win32crypt.CryptUnprotectData(blob,None,None,None,0)[1].decode()

def _form_post(url,fields,timeout=15):
    data=urllib.parse.urlencode(fields).encode()
    req=urllib.request.Request(url,data=data,method="POST",headers={"Content-Type":"application/x-www-form-urlencoded"})
    with urllib.request.urlopen(req,timeout=timeout) as r:return json.loads(r.read().decode())

def _graph_get(path,params,token,timeout=15):
    q=dict(params);q["access_token"]=token
    url=f"https://graph.facebook.com/{GRAPH_VERSION}"+path+"?"+urllib.parse.urlencode(q)
    req=urllib.request.Request(url,method="GET")
    with urllib.request.urlopen(req,timeout=timeout) as r:return json.loads(r.read().decode())

def read_only_preflight(user_token,graph_get=_graph_get):
    try: pages=graph_get("/me/accounts",{"fields":"name,access_token,tasks"},user_token)["data"]
    except Exception:return MetaPreflightResult("HOLD","HOLD","HOLD")
    page=next((p for p in pages if str(p.get("id"))==PAGE_ID),None)
    if not page:return MetaPreflightResult("PASS","HOLD","HOLD")
    tasks=set(page.get("tasks") or [])
    access="PASS" if ({"CREATE_CONTENT","PROFILE_PLUS_CREATE_CONTENT"} & tasks) else "HOLD"
    return MetaPreflightResult("PASS","PASS",access)

def build_authorization_url(state):
    q={"client_id":APP_ID,"redirect_uri":META_REDIRECT_URI,"state":state,
       "response_type":"code","scope":",".join(SCOPES)}
    return AUTH_ENDPOINT+"?"+urllib.parse.urlencode(q)

def register_transaction(tx,state,post=_form_post):
    r=post(EXCHANGE_BASE,{"action":"register","tx":tx,"state":state})
    if r.get("status")!="PASS": raise RuntimeError("REGISTER_HOLD")

def poll_handoff(tx,post=_form_post,timeout=300,interval=2):
    end=time.time()+timeout
    while time.time()<end:
        r=post(EXCHANGE_BASE,{"action":"poll","tx":tx})
        if r.get("status")=="PASS" and isinstance(r.get("handoff"),str) and r["handoff"]:return r["handoff"]
        if r.get("status") not in ("WAIT","PASS"):raise RuntimeError("POLL_HOLD")
        time.sleep(interval)
    raise RuntimeError("POLL_TIMEOUT")

def redeem_handoff(handoff,tx,post=_form_post):
    r=post(EXCHANGE_BASE,{"action":"redeem","handoff":handoff,"tx":tx})
    token=r.get("credential") if r.get("status")=="PASS" else None
    if not isinstance(token,str) or not token:raise RuntimeError("REDEEM_HOLD")
    return token

def connect_facebook(token_path,open_browser=webbrowser.open,post=_form_post,graph_get=_graph_get,poll=poll_handoff):
    tx=secrets.token_urlsafe(24);state=secrets.token_urlsafe(32)
    register_transaction(tx,state,post)
    if not open_browser(build_authorization_url(state)):raise RuntimeError("BROWSER_OPEN_HOLD")
    handoff=poll(tx,post);token=redeem_handoff(handoff,tx,post)
    store=ProtectedTokenStore(token_path);store.save(token)
    return read_only_preflight(store.load(),graph_get)
