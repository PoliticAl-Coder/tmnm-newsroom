"""TMNM source-only recovery collector — review build.

Captures approved source bytes once, scans/hashes/archives those same bytes.
No network calls, deployment or publishing. Current-machine execution requires
separate authority.
"""
from __future__ import annotations
import hashlib, json, os, re, stat, tempfile, uuid, zipfile
from pathlib import Path

MAX_BYTES = 2_000_000
SOURCE_DIRS = ("ControlRoom", "LocalWorker")
REQUIRED_GROUPS = ("ControlRoom", "LocalWorker")
PUBLISH_RE=re.compile(r"(?i)(facebook|publisher|publish_once|payload_for|validate_actionable|canonical_snapshot|workflowstore)")
OWNER8766_RE=re.compile(r"(?i)(8766|owner.?console)")
ALLOWED = {".py",".js",".mjs",".cjs",".html",".htm",".css",".ps1",".cmd",".bat",".vbs",".txt",".md"}
EXCLUDE_DIRS = {".git",".venv","venv","__pycache__","node_modules","secrets","secret","state","logs","log","cache","tmp","temp","downloads","evidence","results"}
EXCLUDE_NAME_RE = re.compile(r"(?i)(token|credential|oauth|cookie|session|\.env(?:\.|$)|config(?:\.|$)|secret|keyring|keystore|database|\.db$|\.sqlite)")
SECRET_ASSIGN_RE = re.compile(r"""(?ix)
(?:"|\')?(?:access[_-]?token|refresh[_-]?token|client[_-]?secret|api[_-]?key|app[_-]?secret|private[_-]?key|password|passwd|pwd|authorization)(?:"|\')?\s*[:=]\s*["\']([^"\']{8,})["\']
""")
SECRET_VALUE_RE = re.compile(
    r"(?i)(?:ya29\.[A-Za-z0-9_.~+/=-]{10,}|1//[A-Za-z0-9_.~+/=-]{10,}|"
    r"GOCSPX-[A-Za-z0-9_-]{10,}|AIza[0-9A-Za-z_-]{20,}|gh[pousr]_[A-Za-z0-9]{20,}|"
    r"sk-(?:live|proj)-[A-Za-z0-9_-]{16,}|Bearer\s+[A-Za-z0-9._~+/=-]{20,}|"
    r"EA[A-Za-z0-9]{40,}|-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----)"
)
PLACEHOLDER_RE = re.compile(r"(?i)^(?:example|placeholder|dummy|test|synthetic|redacted|changeme|your[_ -].*|<.*>|\$\{.*\})$")

class CollectorError(RuntimeError): pass

def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest().upper()

def absolute_localappdata(env=None) -> Path:
    env = os.environ if env is None else env
    raw = env.get("LOCALAPPDATA", "")
    p = Path(raw)
    if not raw or not p.is_absolute():
        raise CollectorError("LOCALAPPDATA_NOT_ABSOLUTE")
    return p

def has_reparse(path: Path) -> bool:
    st = os.lstat(path)
    attrs = getattr(st, "st_file_attributes", 0)
    rp = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400)
    return stat.S_ISLNK(st.st_mode) or bool(attrs & rp)

def inspect_root_ancestors(path: Path) -> None:
    cur=Path(os.path.abspath(path)); chain=[]
    while True:
        chain.append(cur)
        if cur.parent==cur: break
        cur=cur.parent
    for p in reversed(chain):
        if p.exists() and has_reparse(p): raise CollectorError("REPARSE_ANCESTOR_REJECTED:"+str(p))

def ensure_safe_path(path: Path, root: Path) -> None:
    root_abs = Path(os.path.abspath(root))
    inspect_root_ancestors(root_abs)
    path_abs = Path(os.path.abspath(path))
    try:
        path_abs.relative_to(root_abs)
    except ValueError:
        raise CollectorError("PATH_ESCAPES_APPROVED_ROOT")
    cur = root_abs
    if has_reparse(cur):
        raise CollectorError("REPARSE_POINT_REJECTED:" + str(cur))
    for part in path_abs.relative_to(root_abs).parts:
        cur = cur / part
        if has_reparse(cur):
            raise CollectorError("REPARSE_POINT_REJECTED:" + str(cur))

def secret_reason(text: str) -> str | None:
    if SECRET_VALUE_RE.search(text):
        return "KNOWN_SECRET_FORMAT"
    for m in SECRET_ASSIGN_RE.finditer(text):
        value = m.group(1).strip()
        if not PLACEHOLDER_RE.match(value):
            return "SECRET_ASSIGNMENT"
    return None

def capture_file(path: Path, root: Path) -> tuple[bytes,str]:
    ensure_safe_path(path, root)
    try:
        size = path.stat().st_size
    except OSError as e:
        raise CollectorError("UNREADABLE:" + str(path)) from e
    if size > MAX_BYTES:
        raise CollectorError("OVERSIZED:" + str(path))
    try:
        data = path.read_bytes()
    except OSError as e:
        raise CollectorError("UNREADABLE:" + str(path)) from e
    if len(data) != size:
        raise CollectorError("SIZE_CHANGED_DURING_CAPTURE:" + str(path))
    try:
        text = data.decode("utf-8-sig", errors="strict")
    except UnicodeDecodeError as e:
        raise CollectorError("UNDECODABLE:" + str(path)) from e
    reason = secret_reason(text)
    if reason:
        raise CollectorError(reason + ":" + str(path))
    return data, text

def walk_source_dir(base: Path, root: Path):
    if not base.exists() or not base.is_dir():
        raise CollectorError("MISSING_REQUIRED_SOURCE:" + base.name)
    ensure_safe_path(base, root)
    def walk_error(e): raise CollectorError("TRAVERSAL_ERROR:"+str(e))
    for current, dirs, files in os.walk(base, topdown=True, followlinks=False, onerror=walk_error):
        cur = Path(current)
        ensure_safe_path(cur, root)
        kept=[]
        for d in dirs:
            p=cur/d
            if d.lower() in EXCLUDE_DIRS:
                continue
            ensure_safe_path(p, root)
            kept.append(d)
        dirs[:] = kept
        for name in files:
            p=cur/name
            ensure_safe_path(p, root)
            if p.suffix.lower() not in ALLOWED or EXCLUDE_NAME_RE.search(name):
                continue
            yield p

def collect(root: Path) -> list[tuple[Path,bytes]]:
    inspect_root_ancestors(root)
    ensure_safe_path(root, root)
    captured=[]; seen_groups=set(); publishing=False; owner8766=False
    for dirname in SOURCE_DIRS:
        base=root/dirname; group_files=0
        for p in walk_source_dir(base, root):
            data,text = capture_file(p, root)
            captured.append((p.relative_to(root), data)); group_files += 1
            publishing = publishing or bool(PUBLISH_RE.search(text) or PUBLISH_RE.search(str(p)))
            owner8766 = owner8766 or bool(OWNER8766_RE.search(text) or OWNER8766_RE.search(str(p)))
        if group_files == 0: raise CollectorError("MISSING_REQUIRED_SOURCE:" + dirname)
        seen_groups.add(dirname)
    if set(REQUIRED_GROUPS) - seen_groups or not captured: raise CollectorError("EMPTY_OUTPUT")
    if not publishing: raise CollectorError("MISSING_PUBLISHING_ENTRYPOINT")
    if not owner8766: raise CollectorError("MISSING_8766_OWNER_CONSOLE_SOURCE")
    return captured


def write_archive(captured, output_dir: Path) -> Path:
    if not captured: raise CollectorError("EMPTY_OUTPUT")
    if not output_dir.is_absolute(): raise CollectorError("OUTPUT_DIR_NOT_ABSOLUTE")
    output_dir.mkdir(parents=True, exist_ok=True)
    name="TMNM_CURRENT_PUBLISHING_SOURCE_ONLY_"+uuid.uuid4().hex+".zip"
    final=output_dir/name; partial=output_dir/(name+".partial"); owned={partial,final}; manifest=[]
    try:
        with zipfile.ZipFile(partial,"x",zipfile.ZIP_DEFLATED) as z:
            for rel,data in captured:
                arc=str(rel).replace("\\","/"); z.writestr(arc,data)
                manifest.append({"path":arc,"sha256":digest(data),"size":len(data)})
            z.writestr("SOURCE_MANIFEST.json",json.dumps({"schema":"TMNM_SOURCE_RECOVERY_V3","files":sorted(manifest,key=lambda x:x["path"].lower()),"secret_scan":"PASS","capture_semantics":"scan/hash/archive same captured bytes"},indent=2).encode("utf-8"))
        if final.exists(): raise CollectorError("UNIQUE_OUTPUT_COLLISION")
        partial.rename(final); return final
    except Exception:
        errors=[]
        for p in owned:
            if p.exists():
                try:p.unlink()
                except OSError as e:errors.append(str(e))
        if errors: raise CollectorError("CLEANUP_FAILED:"+";".join(errors))
        raise

def main() -> int:
    try:
        if os.name!="nt": raise CollectorError("NATIVE_WINDOWS_REQUIRED")
        local=absolute_localappdata(); inspect_root_ancestors(local); root=local/"TMNM"
        if not root.is_dir(): raise CollectorError("TMNM_ROOT_MISSING")
        captured=collect(root)
        output_dir=Path(tempfile.mkdtemp(prefix="TMNM_Source_Recovery_")).resolve()
        try: output_dir.relative_to(root.resolve()); raise CollectorError("OUTPUT_INSIDE_INSTALLED_TREE")
        except ValueError: pass
        final=write_archive(captured,output_dir)
        archive_hash=digest(final.read_bytes())
        print("FILES="+str(len(captured))); print("ZIP="+str(final)); print("ZIP_SHA256="+archive_hash); print("STATUS=PASS")
        return 0
    except Exception as e:
        print("STATUS=FAIL"); print("ERROR="+str(e)); return 2

if __name__=="__main__": raise SystemExit(main())
