"""MASTER389 exact-file recovery. Reads one existing MASTER384 result only."""
from __future__ import annotations
import argparse, base64, ctypes, json, os, re
from ctypes import wintypes
from pathlib import Path

EXACT_INPUT=Path(r"C:\Users\USER\AppData\Local\TMNM\LocalWorker\state\tech_results_outbox\TMNM_MASTER384_APPS_SCRIPT_READONLY_RESULT.json")
EXACT_CRED=Path(r"C:\Users\USER\AppData\Local\TMNM\ControlRoom\secrets\publisher_google_token.dpapi")
ALLOWED_TOP={"result","snapshot","drive_persistence"}
ALLOWED_RESULT={"CURRENT_HEAD","CURRENT_DEPLOYED_VERSION","CURRENT_DEPLOYED_HASH","V16B_COMPARISON","GOOGLE_AUTH","MUTATIONS","SCRIPTS_RUN","META_CALLS","script_id","deployment_id","credential_file","error"}
SECRET_KEYS=re.compile(r"(?i)(access[_-]?token|refresh[_-]?token|client[_-]?secret|authorization|cookie|api[_-]?key|password)")
SECRET_TEXT=re.compile(r"(?i)(bearer\s+[A-Za-z0-9._~+/-]+|ya29\.[A-Za-z0-9._-]+)")
class DATA_BLOB(ctypes.Structure): _fields_=[("cbData",wintypes.DWORD),("pbData",ctypes.POINTER(ctypes.c_byte))]
def dpapi_unprotect(blob):
    if os.name!="nt": raise RuntimeError("WINDOWS_REQUIRED")
    inp=(ctypes.c_byte*len(blob)).from_buffer_copy(blob); ib=DATA_BLOB(len(blob),inp); ob=DATA_BLOB()
    if not ctypes.windll.crypt32.CryptUnprotectData(ctypes.byref(ib),None,None,None,None,0,ctypes.byref(ob)): raise RuntimeError("DPAPI_DECRYPT_FAILED")
    try:return ctypes.string_at(ob.pbData,ob.cbData)
    finally:ctypes.windll.kernel32.LocalFree(ob.pbData)
def decode_credential(raw):
    cs=[raw]
    try: cs.append(base64.b64decode(raw,validate=True))
    except Exception: pass
    for c in cs:
        try:
            d=json.loads(c.decode("utf-8-sig"))
            if isinstance(d,dict) and ("refresh_token" in d or "token" in d): return d
        except Exception: pass
    raise RuntimeError("CREDENTIAL_FORMAT_UNRECOGNISED")
def validate(d):
    if not isinstance(d,dict) or set(d)-ALLOWED_TOP: raise ValueError("UNEXPECTED_SCHEMA_TOP")
    if not isinstance(d.get("result"),dict) or set(d["result"])-ALLOWED_RESULT: raise ValueError("UNEXPECTED_SCHEMA_RESULT")
    if d.get("snapshot") is not None and not isinstance(d["snapshot"],dict): raise ValueError("UNEXPECTED_SCHEMA_SNAPSHOT")
    if "drive_persistence" in d and not isinstance(d["drive_persistence"],dict): raise ValueError("UNEXPECTED_SCHEMA_PERSISTENCE")
def sanitise(v):
    if isinstance(v,dict): return {k:("[REDACTED]" if SECRET_KEYS.search(str(k)) else sanitise(x)) for k,x in v.items()}
    if isinstance(v,list): return [sanitise(x) for x in v]
    if isinstance(v,str): return SECRET_TEXT.sub("[REDACTED]",v)
    return v
def persist(payload,info,drive_factory=None):
    if drive_factory is None:
        from google.oauth2.credentials import Credentials
        from google.auth.transport.requests import Request
        from googleapiclient.discovery import build
        from googleapiclient.http import MediaInMemoryUpload
        scopes=set(info.get("scopes") or info.get("scope","").split())
        if not ({"https://www.googleapis.com/auth/drive","https://www.googleapis.com/auth/drive.file"} & scopes): raise RuntimeError("REQUIRED_EXISTING_SCOPE_MISSING: drive")
        creds=Credentials.from_authorized_user_info(info); creds.refresh(Request())
        drive=build("drive","v3",credentials=creds,cache_discovery=False)
        media=MediaInMemoryUpload(json.dumps(payload,ensure_ascii=False,indent=2).encode(),mimetype="application/json",resumable=False)
    else:
        drive,media=drive_factory(info,payload)
    c=drive.files().create(body={"name":"TMNM_MASTER384_RECOVERED_RESULT.json","mimeType":"application/json"},media_body=media,fields="id,name").execute()
    g=drive.files().get(fileId=c["id"],fields="id,name,size").execute()
    return {"id":g["id"],"verified":True}
def run(argv=None,persist_fn=persist,credential_loader=None):
    p=argparse.ArgumentParser(); p.add_argument("--input",required=True); p.add_argument("--credential",default=str(EXACT_CRED)); a=p.parse_args(argv)
    try:
        inp=Path(a.input)
        if str(inp).lower()!=str(EXACT_INPUT).lower(): raise RuntimeError("ALTERNATE_INPUT_PATH_REJECTED")
        before=inp.read_bytes(); d=json.loads(before.decode("utf-8-sig")); validate(d); clean=sanitise(d)
        info=(credential_loader or (lambda p:decode_credential(dpapi_unprotect(p.read_bytes()))))(Path(a.credential))
        r=persist_fn(clean,info)
        if inp.read_bytes()!=before: raise RuntimeError("ORIGINAL_FILE_CHANGED")
        print("TMNM_MASTER389_STATUS=PASS"); print("DRIVE_FILE_ID="+r["id"]); return 0
    except Exception as e:
        print("TMNM_MASTER389_STATUS=HOLD"); print("ERROR_CLASS="+type(e).__name__+":"+str(e)[:180]); return 2
if __name__=="__main__": raise SystemExit(run())
