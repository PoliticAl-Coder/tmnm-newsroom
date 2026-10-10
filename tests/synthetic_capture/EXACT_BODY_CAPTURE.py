"""Fail-closed, bounded, exact-body source review. Python 3.8+ standard library.
No network, import of target modules, subprocess, host writes or credentials.
Designed for separately authorised acquisition; not owner-run approved.
"""
import ast,hashlib,json,os,pathlib,re,sys,zipfile
ROOT_NAMES={
 'backend':('ControlRoom/control_room/app.py',('_refresh','_refresh_uncached','_tmnm_v73_cached_canonical','_tmnm_v73_refresh_one')),
 'frontend':('OwnerConsole/tmnm_owner_console/app.py',('inventory_destination','resolve_canonical_package','_qc943_reconcile_publication')),
 'claim':('LocalWorker/app/commission_claim_bridge.py',('process_claim','generic_worker_execute','worker_execute','lifecycle_probe')),
 'consumer':('LocalWorker/app/editorial_consumer.py',('process','process_generic_article','stage_package')),
}
MAX_SOURCE=3_000_000; MAX_LINES=180; MAX_FUNCTION_BYTES=12000; MAX_TOTAL=36000
SECRET=re.compile(r'(?i)(?:password|passwd|token|api[_-]?key|bearer|client[_-]?secret|private[_-]?key|credential|authorization|oauth|cookie|session|smtp|refresh[_-]?token|google_auth|\.env\b|service[_-]?account)')
# Sensitive values and keys MUST fail closed: do not silently redact transaction code.
SECRET_VALUE=re.compile(r'(?i)(?:-----BEGIN [A-Z ]*PRIVATE KEY-----|gh[pousr]_[A-Za-z0-9]{12,}|AIza[A-Za-z0-9_-]{20,}|Bearer\s+[A-Za-z0-9._-]{10,})')

# AST-aware, fail-closed source export policy. Never emit rejected data.
SENSITIVE_TERMS = (
    'password','passwd','passphrase','secret','credential','authorization','authkey',
    'apikey','accesskey','privatekey','recoverycode','recoverykey','backupcode',
    'token','oauth','cookie','session','smtp','googleauth','serviceaccount',
    'seedphrase','mnemonic','totp','otpsecret','clientsecret','environ',
)
ENV_MODULES = {'os', 'dotenv', 'keyring', 'secrets'}

def _collapsed(value):
    return re.sub(r'[^a-z0-9]', '', value.casefold())

def _sensitive_name(value):
    name = _collapsed(value)
    return any(term in name for term in SENSITIVE_TERMS)

def _constant_text(node):
    if isinstance(node,ast.Constant) and isinstance(node.value,(str,bytes)):
        return node.value.decode('utf-8','ignore') if isinstance(node.value,bytes) else node.value
    if isinstance(node,ast.JoinedStr):
        return ''.join(_constant_text(v) or '' for v in node.values)
    if isinstance(node,ast.BinOp) and isinstance(node.op,ast.Add):
        left,right=_constant_text(node.left),_constant_text(node.right)
        if left is not None and right is not None:return left+right
    if isinstance(node,(ast.List,ast.Tuple)):
        vals=[_constant_text(x) for x in node.elts]
        if vals and all(x is not None for x in vals):return ''.join(vals)
    return None

def _privacy_check(body):
    # Static scanner is intentionally conservative about dynamic source extraction.
    # No rejected source content is included in messages or diagnostics.
    if SECRET.search(body) or SECRET_VALUE.search(body):
        raise ValueError('SENSITIVE_SOURCE')
    tree=ast.parse(body)
    for node in ast.walk(tree):
        if isinstance(node,(ast.Name,ast.Attribute,ast.arg)):
            val = node.id if isinstance(node,ast.Name) else (node.attr if isinstance(node,ast.Attribute) else node.arg)
            if _sensitive_name(val):raise ValueError('SENSITIVE_SOURCE')
        if isinstance(node,ast.Constant) and isinstance(node.value,(str,bytes)):
            literal=_constant_text(node)
            if SECRET_VALUE.search(literal) or _sensitive_name(literal):
                raise ValueError('SENSITIVE_SOURCE')
        if isinstance(node,(ast.BinOp,ast.JoinedStr,ast.List,ast.Tuple)):
            folded=_constant_text(node)
            if folded is not None and _sensitive_name(folded):raise ValueError('SENSITIVE_SOURCE')
        if isinstance(node,ast.Call):
            func=node.func
            if isinstance(func,ast.Name) and func.id in {'getattr','setattr','eval','exec','globals','locals','vars','__import__'}:
                raise ValueError('DYNAMIC_SOURCE_ACCESS')
            if isinstance(func,ast.Attribute) and func.attr in {'getenv','getpass','read_text','read_bytes'}:
                # File reads or environment lookups may expose unreviewed private data.
                raise ValueError('DYNAMIC_SOURCE_ACCESS')
        if isinstance(node,ast.Subscript) and isinstance(node.value,ast.Attribute):
            if node.value.attr in {'environ','environb'}:raise ValueError('DYNAMIC_SOURCE_ACCESS')
    return True

def sha(raw): return hashlib.sha256(raw).hexdigest()
def inspect_one(root,role,expected):
    rel,names=ROOT_NAMES[role]; base=root.resolve(strict=True); path=root.joinpath(*rel.split('/'))
    if not path.is_file() or path.is_symlink(): raise ValueError('MISSING_OR_LINK:'+role)
    # Reject symlinked ancestors and any escape from the fixed root.
    for ancestor in (path,)+tuple(path.parents):
        if ancestor==root.parent:break
        if ancestor.is_symlink():raise ValueError('SYMLINK:'+role)
    if not str(path.resolve(strict=True)).startswith(str(base)+os.sep):raise ValueError('ESCAPE:'+role)
    raw=path.read_bytes()
    if len(raw)>MAX_SOURCE:raise ValueError('FILE_TOO_LARGE:'+role)
    if sha(raw)!=expected:raise ValueError('HASH_MISMATCH:'+role)
    src=raw.decode('utf-8-sig'); lines=src.splitlines(keepends=True)
    tree=ast.parse(src)
    candidates=[node for node in tree.body if isinstance(node,(ast.FunctionDef,ast.AsyncFunctionDef)) and node.name in names]
    found={}; total=0
    for node in candidates:
        if node.name in found:raise ValueError('DUPLICATE_FUNCTION:'+role)
        start=node.lineno; end=node.end_lineno
        if not end or end-start+1>MAX_LINES:raise ValueError('UNBOUNDED_FUNCTION:'+role)
        body=''.join(lines[start-1:end]); b=body.encode('utf-8')
        if len(b)>MAX_FUNCTION_BYTES:raise ValueError('BODY_TOO_LARGE:'+role)
        _privacy_check(body)
        total+=len(b)
        found[node.name]={'start':start,'end':end,'sha256':sha(b),'body':body}
    if not found:raise ValueError('NO_APPROVED_FUNCTIONS:'+role)
    return {'relative_path':rel,'source_sha256':sha(raw),'source_bytes':len(raw),'functions':found},total

def capture(root,expected):
    if set(expected)!=set(ROOT_NAMES):raise ValueError('MANIFEST_ROLES_MISMATCH')
    if not isinstance(root,pathlib.Path):root=pathlib.Path(root)
    result={'schema':'TMNM_EXACT_BODY_V1','files':{}}; count=0
    for role in ROOT_NAMES:
        value,num=inspect_one(root,role,expected[role]);count+=num
        if count>MAX_TOTAL:raise ValueError('TOTAL_EXCEEDED')
        result['files'][role]=value
    blob=json.dumps(result,sort_keys=True,ensure_ascii=True).encode()
    if len(blob)>MAX_TOTAL+6000:raise ValueError('JSON_OUTPUT_EXCEEDED')
    return result

def main():
    # Paths and fingerprints supplied via independently checked manifest, never discovered.
    directory=pathlib.Path(__file__).resolve().parent
    try:
        manifest=json.loads((directory/'APPROVED_SOURCE_SHA256.json').read_text(encoding='utf-8'))
        root=pathlib.Path(os.environ['TMNM_SOURCE_ROOT'])
        result=capture(root,manifest)
        encoded=json.dumps(result,sort_keys=True,indent=2).encode('utf-8')
        if len(encoded)>MAX_TOTAL+12000:raise ValueError('PRETTY_OUTPUT_EXCEEDED')
        tmp=directory/'RESULT.json.tmp';tmp.write_bytes(encoded);os.replace(str(tmp),str(directory/'RESULT.json'))
        with zipfile.ZipFile(str(directory/'RESULT.zip.tmp'),'w',zipfile.ZIP_DEFLATED) as z:z.write(str(directory/'RESULT.json'),arcname='RESULT.json')
        os.replace(str(directory/'RESULT.zip.tmp'),str(directory/'RESULT.zip'))
        print('CAPTURE_PASS; RESULT_SHA256='+sha(encoded))
        return 0
    except (ValueError,KeyError,TypeError,OSError,UnicodeError,SyntaxError,JSONDecodeError) as e:
        # Fail closed: remove stale results to prevent old results being mistaken for fresh.
        for leaf in ('RESULT.json','RESULT.zip','RESULT.json.tmp','RESULT.zip.tmp'):
            try:(directory/leaf).unlink(missing_ok=True)
            except OSError:pass
        print('CAPTURE_HOLD; REASON='+type(e).__name__)
        return 4
JSONDecodeError=json.JSONDecodeError
if __name__=='__main__':sys.exit(main())
