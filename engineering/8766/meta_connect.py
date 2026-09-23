"""TMNM 8766 Meta CONNECT client — /exec callback engineering proof. GET-only discovery; no Facebook write endpoints."""
from __future__ import annotations
import json, os, secrets, time, urllib.parse, urllib.request, shutil, subprocess
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

_SAFE_BROWSER_DIAGNOSTICS=[]
def get_safe_browser_diagnostics(): return list(_SAFE_BROWSER_DIAGNOSTICS)

def _browser_candidates(which=shutil.which, environ=os.environ, exists=os.path.isfile, registry_reader=None):
    """Return safe (browser, path, private_flag, source) candidates. No OAuth data."""
    out=[];seen=set()
    def add(name,path,flag,source):
        if path:
            path=os.path.expandvars(str(path).strip().strip('"'))
            key=path.lower()
            if key not in seen and exists(path):
                seen.add(key);out.append((name,path,flag,source))
    # PATH is only one source; normal Windows installs often do not publish browsers there.
    add("EDGE",which("msedge.exe"),"--inprivate","PATH")
    add("CHROME",which("chrome.exe"),"--incognito","PATH")
    roots=[environ.get("PROGRAMFILES(X86)"),environ.get("PROGRAMFILES"),environ.get("LOCALAPPDATA")]
    for root in roots:
        if root:
            add("EDGE",os.path.join(root,"Microsoft","Edge","Application","msedge.exe"),"--inprivate","INSTALL_PATH")
            add("CHROME",os.path.join(root,"Google","Chrome","Application","chrome.exe"),"--incognito","INSTALL_PATH")
    if registry_reader is None and os.name=="nt":
        def registry_reader(exe):
            try:
                import winreg
                sub=r"SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\App Paths\\"+exe
                for hive in (winreg.HKEY_CURRENT_USER,winreg.HKEY_LOCAL_MACHINE):
                    for view in (0,getattr(winreg,"KEY_WOW64_32KEY",0),getattr(winreg,"KEY_WOW64_64KEY",0)):
                        try:
                            with winreg.OpenKey(hive,sub,0,winreg.KEY_READ|view) as k:return winreg.QueryValueEx(k,None)[0]
                        except OSError:pass
            except Exception:pass
            return None
    if registry_reader:
        add("EDGE",registry_reader("msedge.exe"),"--inprivate","APP_PATHS")
        add("CHROME",registry_reader("chrome.exe"),"--incognito","APP_PATHS")
    return out

def open_private_browser(url, which=shutil.which, popen=subprocess.Popen, environ=os.environ,
                         exists=os.path.isfile, registry_reader=None, diagnostic=None):
    _SAFE_BROWSER_DIAGNOSTICS.clear()
    external=diagnostic
    def diagnostic(msg):
        _SAFE_BROWSER_DIAGNOSTICS.append(msg)
        if external: external(msg)
    if not isinstance(url,str) or not url.startswith(AUTH_ENDPOINT+"?"): raise RuntimeError("BROWSER_URL_HOLD")
    if "/u/0/" in url or "/u/1/" in url: raise RuntimeError("ACCOUNT_INDEX_URL_HOLD")
    candidates=_browser_candidates(which,environ,exists,registry_reader)
    if diagnostic:
        diagnostic("BROWSER_CANDIDATES_CHECKED="+(",".join(x[0]+":"+x[3] for x in candidates) or "NONE"))
    # Edge preferred regardless of discovery source, then Chrome.
    candidates.sort(key=lambda x:0 if x[0]=="EDGE" else 1)
    for name,path,flag,source in candidates:
        if diagnostic: diagnostic("BROWSER_LAUNCH_STAGE=TRY_"+name)
        try:
            popen([path,flag,url],close_fds=True)
            if diagnostic:
                diagnostic("BROWSER_SELECTED="+name)
                diagnostic("BROWSER_LAUNCH_STAGE=STARTED")
            return True
        except OSError as e:
            if diagnostic: diagnostic("BROWSER_LAUNCH_ERROR="+name+"_OSERROR_"+str(getattr(e,"winerror",None) or getattr(e,"errno",None) or "UNKNOWN"))
    if diagnostic:
        diagnostic("BROWSER_SELECTED=NONE")
        diagnostic("BROWSER_LAUNCH_STAGE=HOLD")
    raise RuntimeError("PRIVATE_BROWSER_UNAVAILABLE")

def connect_facebook(token_path,open_browser=open_private_browser,post=_form_post,graph_get=_graph_get,poll=poll_handoff):
    tx=secrets.token_urlsafe(24);state=secrets.token_urlsafe(32)
    register_transaction(tx,state,post)
    if not open_browser(build_authorization_url(state)):raise RuntimeError("BROWSER_OPEN_HOLD")
    handoff=poll(tx,post);token=redeem_handoff(handoff,tx,post)
    store=ProtectedTokenStore(token_path);store.save(token)
    return read_only_preflight(store.load(),graph_get)
