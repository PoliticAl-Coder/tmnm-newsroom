"""TMNM source-only recovery collector for Master inspection.

READ-ONLY against the installed TMNM tree. Produces a source-only ZIP plus
manifest in the current working directory. It never reads or copies known
credential files, databases, runtime state, logs, caches, virtualenvs or media.

No network calls. No deployment. No publishing.
"""
from __future__ import annotations
import hashlib, json, os, re, shutil, sys, tempfile, zipfile
from pathlib import Path

ROOT = Path(os.environ.get("LOCALAPPDATA", "")) / "TMNM"
ALLOWED = {".py",".js",".mjs",".cjs",".html",".htm",".css",".ps1",".cmd",".bat",".vbs",".txt",".md"}
EXCLUDE_DIRS = {
    ".git",".venv","venv","__pycache__","node_modules","secrets","secret",
    "state","logs","log","cache","tmp","temp","downloads","evidence","results",
}
EXCLUDE_NAME_RE = re.compile(
    r"(?i)(token|credential|client[_-]?secret|oauth|cookie|session|\.env$|config\.(?:json|ya?ml|toml)$)"
)
SENSITIVE_LITERAL_RE = re.compile(
    r"(?i)(?:ya29\.[A-Za-z0-9_.~+/=-]{10,}|1//[A-Za-z0-9_.~+/=-]{10,}|"
    r"GOCSPX-[A-Za-z0-9_-]{10,}|Bearer\s+[A-Za-z0-9._~+/=-]{20,}|"
    r"EA[A-Za-z0-9]{40,}|-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----|"
    r"[\"']?(?:access_token|refresh_token|client_secret|private_key|password)[\"']?\s*[:=]\s*[\"'][^\"']{8,}[\"'])"
)
RELEVANT_RE = re.compile(r"(?i)(8765|8766|facebook|publisher|publish_once|control.?room|owner.?console|localworker|workflowstore|payload_for|canonical_snapshot|validate_actionable)")

def sha256(p: Path) -> str:
    h=hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda:f.read(1024*1024), b""): h.update(chunk)
    return h.hexdigest().upper()

def excluded(p: Path) -> bool:
    rel=p.relative_to(ROOT)
    if any(part.lower() in EXCLUDE_DIRS for part in rel.parts[:-1]): return True
    if p.suffix.lower() not in ALLOWED: return True
    if EXCLUDE_NAME_RE.search(p.name): return True
    return False

def main() -> int:
    if os.name != "nt" or not ROOT.is_dir():
        print("STATUS=FAIL\nERROR=NATIVE_WINDOWS_TNMN_ROOT_REQUIRED")
        return 2
    selected=[]
    blocked=[]
    for p in ROOT.rglob("*"):
        if not p.is_file() or excluded(p): continue
        try:
            if p.stat().st_size > 2_000_000: continue
            raw=p.read_bytes()
            text=raw.decode("utf-8-sig", errors="replace")
        except OSError:
            continue
        rel=p.relative_to(ROOT)
        primary=rel.parts and rel.parts[0].lower() in {"controlroom","localworker"}
        relevant=primary or bool(RELEVANT_RE.search(text)) or bool(RELEVANT_RE.search(str(rel)))
        if not relevant: continue
        if SENSITIVE_LITERAL_RE.search(text):
            blocked.append(str(rel))
            continue
        selected.append((p,rel))
    if blocked:
        print("STATUS=FAIL")
        print("SECRET_SCAN=BLOCKED")
        for x in blocked: print("BLOCKED_FILE="+x)
        return 3
    out=Path.cwd()
    stage=Path(tempfile.mkdtemp(prefix="TMNM_SOURCE_ONLY_"))
    try:
        manifest=[]
        for src,rel in selected:
            dst=stage/rel
            dst.parent.mkdir(parents=True,exist_ok=True)
            shutil.copy2(src,dst)
            manifest.append({"path":str(rel).replace("\\","/"),"sha256":sha256(dst),"size":dst.stat().st_size})
        manifest.sort(key=lambda x:x["path"].lower())
        (stage/"SOURCE_MANIFEST.json").write_text(json.dumps({
            "schema":"TMNM_SOURCE_RECOVERY_V1",
            "source_root":"%LOCALAPPDATA%/TMNM",
            "files":manifest,
            "excluded":"credentials/config secrets/databases/runtime state/logs/caches/venvs/media",
            "secret_scan":"PASS"
        },indent=2),encoding="utf-8")
        zip_path=out/"TMNM_CURRENT_PUBLISHING_SOURCE_ONLY.zip"
        if zip_path.exists(): zip_path.unlink()
        with zipfile.ZipFile(zip_path,"w",zipfile.ZIP_DEFLATED) as z:
            for p in sorted(stage.rglob("*")):
                if p.is_file(): z.write(p,p.relative_to(stage))
        print("STATUS=PASS")
        print("SECRET_SCAN=PASS")
        print("FILES="+str(len(selected)))
        print("ZIP="+str(zip_path))
        print("ZIP_SHA256="+sha256(zip_path))
        return 0
    finally:
        shutil.rmtree(stage,ignore_errors=False)

if __name__=="__main__":
    raise SystemExit(main())
