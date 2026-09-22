"""TMNM MASTER384 read-only Apps Script management inspector.

READ ONLY: Apps Script projects.getContent, deployments.get, versions.get.
NEVER calls scripts.run and contains no Apps Script mutation method.
Owner execution is NOT authorised by this source package alone.
"""
from __future__ import annotations
import argparse, base64, ctypes, hashlib, json, os, re, sys
from ctypes import wintypes
from pathlib import Path

SCRIPT_ID="1KxRzkW4EwdSROMdx-yXXH9njJsfXnhcxF9-SabgvZ85yWbMZnifs8nAT"
DEPLOYMENT_ID="AKfycbyRr1KP_B5aMfgLd2d4TGhJ5jpmVTD5HKTv75RkvAQmtXe7-aWK1TThjppLFMs5ntM"
V16B_VERSION=24
V16B_SHA="54724723afa3b8d3dcdbe02e71973a090f51675954981d08ada6f15a7021a21f"
SCOPES_ALLOWED={
 "https://www.googleapis.com/auth/script.projects",
 "https://www.googleapis.com/auth/drive",
 "https://www.googleapis.com/auth/gmail.labels",
 "https://www.googleapis.com/auth/script.external_request",
 "https://www.googleapis.com/auth/script.scriptapp",
}
FORBIDDEN_TEXT=re.compile(r"(?i)(access_token|refresh_token|client_secret|authorization\s*:|bearer\s+[A-Za-z0-9._~+/-]+)")
class DATA_BLOB(ctypes.Structure):
    _fields_=[("cbData",wintypes.DWORD),("pbData",ctypes.POINTER(ctypes.c_byte))]
def dpapi_unprotect(blob:bytes)->bytes:
    if os.name!="nt": raise RuntimeError("WINDOWS_REQUIRED")
    inp=(ctypes.c_byte*len(blob)).from_buffer_copy(blob); ib=DATA_BLOB(len(blob),inp); ob=DATA_BLOB()
    ok=ctypes.windll.crypt32.CryptUnprotectData(ctypes.byref(ib),None,None,None,None,0,ctypes.byref(ob))
    if not ok: raise RuntimeError("DPAPI_DECRYPT_FAILED")
    try: return ctypes.string_at(ob.pbData,ob.cbData)
    finally: ctypes.windll.kernel32.LocalFree(ob.pbData)
def decode_credential(raw:bytes)->dict:
    candidates=[raw]
    try: candidates.append(base64.b64decode(raw,validate=True))
    except Exception: pass
    for c in candidates:
        try:
            d=json.loads(c.decode("utf-8-sig"))
            if isinstance(d,dict) and ("refresh_token" in d or "token" in d): return d
        except Exception: pass
    raise RuntimeError("CREDENTIAL_FORMAT_UNRECOGNISED")
def canonical_files(files)->bytes:
    clean=[]
    for f in files or []:
        clean.append({"name":f.get("name",""),"type":f.get("type",""),"source":f.get("source","")})
    clean.sort(key=lambda x:(x["name"],x["type"]))
    return json.dumps(clean,ensure_ascii=False,sort_keys=True,separators=(",",":")).encode("utf-8")
def content_hash(content)->str: return hashlib.sha256(canonical_files(content.get("files",[]))).hexdigest()
def safe_error(e:Exception)->str:
    s=FORBIDDEN_TEXT.sub("[REDACTED]",str(e))
    return re.sub(r"[A-Za-z0-9_-]{40,}","[REDACTED]",s)[:400]
def inspect(credential_path:Path, service_factory=None, credential_loader=None):
    out={"CURRENT_HEAD":"INDETERMINATE","CURRENT_DEPLOYED_VERSION":"INDETERMINATE","CURRENT_DEPLOYED_HASH":"INDETERMINATE",
         "V16B_COMPARISON":"INDETERMINATE","GOOGLE_AUTH":"FAIL","MUTATIONS":0,"SCRIPTS_RUN":0,"META_CALLS":0,
         "script_id":SCRIPT_ID,"deployment_id":DEPLOYMENT_ID}
    if not credential_path.is_file(): out["error"]="CREDENTIAL_ABSENT"; return out,None,None
    out["credential_file"]="PRESENT"
    try:
        info=(credential_loader or (lambda p: decode_credential(dpapi_unprotect(p.read_bytes()))))(credential_path)
        scopes=set(info.get("scopes") or info.get("scope","").split())
        # Fail closed: management scope must already exist; no incremental auth.
        if "https://www.googleapis.com/auth/script.projects" not in scopes:
            raise RuntimeError("REQUIRED_EXISTING_SCOPE_MISSING: script.projects")
        if service_factory is None:
            from google.oauth2.credentials import Credentials
            from google.auth.transport.requests import Request
            from googleapiclient.discovery import build
            creds=Credentials.from_authorized_user_info(info)
            creds.refresh(Request())
            service=build("script","v1",credentials=creds,cache_discovery=False)
        else: service=service_factory(info)
        out["GOOGLE_AUTH"]="PASS"
        head=service.projects().getContent(scriptId=SCRIPT_ID).execute()
        dep=service.projects().deployments().get(scriptId=SCRIPT_ID,deploymentId=DEPLOYMENT_ID).execute()
        ver=dep.get("deploymentConfig",{}).get("versionNumber")
        if ver is None: raise RuntimeError("DEPLOYMENT_VERSION_MISSING")
        deployed=service.projects().versions().get(scriptId=SCRIPT_ID,versionNumber=int(ver)).execute()
        hh=content_hash(head); dh=content_hash(deployed)
        out["CURRENT_HEAD"]=hh; out["CURRENT_DEPLOYED_VERSION"]=int(ver); out["CURRENT_DEPLOYED_HASH"]=dh
        # V16B SHA algorithm provenance is not assumed. Exact historical SHA comparison is reported only
        # if our deterministic hash happens to equal it; otherwise classify source-hash algorithm mismatch
        # separately rather than falsely claiming source difference.
        if int(ver)!=V16B_VERSION:
            out["V16B_COMPARISON"]="DIFFERENT:DEPLOYED_VERSION"
        elif hh==V16B_SHA and dh==V16B_SHA:
            out["V16B_COMPARISON"]="MATCH"
        elif hh!=dh:
            out["V16B_COMPARISON"]="DIFFERENT:HEAD_VS_DEPLOYED"
        else:
            out["V16B_COMPARISON"]="INDETERMINATE:V16B_HASH_CANONICALISATION_UNPROVEN"
        snap={"head":{"hash":hh,"files":head.get("files",[])},
              "deployment":{"deploymentId":DEPLOYMENT_ID,"deploymentConfig":dep.get("deploymentConfig",{}),"updateTime":dep.get("updateTime")},
              "deployed_version":{"versionNumber":int(ver),"hash":dh,"files":deployed.get("files",[])}}
        return out,snap,info
    except Exception as e:
        out["error"]=safe_error(e); return out,None,None
def persist_evidence(payload:dict, info:dict, title:str, drive_factory=None):
    from google.oauth2.credentials import Credentials
    from google.auth.transport.requests import Request
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaInMemoryUpload
    scopes=set(info.get("scopes") or info.get("scope","").split())
    if not ({"https://www.googleapis.com/auth/drive","https://www.googleapis.com/auth/drive.file"} & scopes):
        raise RuntimeError("REQUIRED_EXISTING_SCOPE_MISSING: drive evidence persistence")
    creds=Credentials.from_authorized_user_info(info); creds.refresh(Request())
    drive=build("drive","v3",credentials=creds,cache_discovery=False)
    data=json.dumps(payload,ensure_ascii=False,indent=2).encode("utf-8")
    media=MediaInMemoryUpload(data,mimetype="application/json",resumable=False)
    created=drive.files().create(body={"name":title,"mimeType":"application/json"},media_body=media,fields="id,name").execute()
    # Verify persistence by metadata readback only; do not echo credential data.
    check=drive.files().get(fileId=created["id"],fields="id,name,size").execute()
    return {"drive_file_id":check["id"],"drive_name":check["name"],"drive_size":check.get("size"),"verified":True}

def run(argv=None, inspect_fn=inspect, persist_fn=persist_evidence):
    p=argparse.ArgumentParser(); p.add_argument("--credential",required=True); p.add_argument("--out",required=True); p.add_argument("--persist-drive",action="store_true"); a=p.parse_args(argv)
    result,snapshot,info=inspect_fn(Path(a.credential))
    payload={"result":result,"snapshot":snapshot,"drive_persistence":{"status":"NOT_REQUESTED","drive_file_id":None}}
    if a.persist_drive:
        payload["drive_persistence"]={"status":"HOLD","drive_file_id":None}
        if result["GOOGLE_AUTH"]=="PASS" and info is not None:
            try:
                receipt=persist_fn({"result":result,"snapshot":snapshot},info,"TMNM_MASTER384_APPS_SCRIPT_READONLY_RESULT.json")
                payload["drive_persistence"]={"status":"PASS","drive_file_id":receipt["drive_file_id"],"verified":bool(receipt.get("verified"))}
            except Exception as e:
                result["error"]="EVIDENCE_PERSISTENCE_FAILED: "+safe_error(e)
                result["GOOGLE_AUTH"]="FAIL"
    Path(a.out).write_text(json.dumps(payload,ensure_ascii=False,indent=2),encoding="utf-8")
    info=None
    ok=result["GOOGLE_AUTH"]=="PASS" and (not a.persist_drive or payload["drive_persistence"]["status"]=="PASS")
    print("TMNM_MASTER384_STATUS="+("PASS" if ok else "HOLD"))
    print("RESULT_FILE="+str(Path(a.out)))
    return 0 if ok else 2
def main(argv=None): return run(argv)
if __name__=="__main__": raise SystemExit(main())
