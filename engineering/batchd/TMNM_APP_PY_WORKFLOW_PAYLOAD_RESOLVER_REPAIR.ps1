$ErrorActionPreference='Stop'
$target='C:\Users\USER\AppData\Local\TMNM\OwnerConsole\CanonicalBridgeReview_579a2cf7a4da5591\tmnm_owner_console\app.py'
$pre='27ae2246fc4cabf87add213e3763d1159bd6078dd7c1f7c6a2cb1e0bc443bc24'
function Get-Sha256([string]$Path){
  $alg=[Security.Cryptography.SHA256]::Create()
  try{$hash=$alg.ComputeHash([IO.File]::ReadAllBytes($Path))}finally{$alg.Dispose()}
  return ([BitConverter]::ToString($hash)).Replace('-','').ToLowerInvariant()
}
if(!(Test-Path -LiteralPath $target)){throw 'TARGET_NOT_FOUND'}
if((Get-Sha256 $target)-ne$pre){throw 'PRE_SHA_MISMATCH'}
$text=[IO.File]::ReadAllText($target)
$old="if u.path=='/api/workflow/payload':`n            pid=str(body.get('package_id') or '')`n            p=CACHE.get(pid)`n            if not p:return self.sendj({'error':'PACKAGE_NOT_IN_CURRENT_VIEW'},404)"
$new="if u.path=='/api/workflow/payload':`n            pid=str(body.get('package_id') or '')`n            p=resolve_canonical_package(pid,allow_cache=True)`n            if not p:return self.sendj({'error':'PACKAGE_NOT_IN_CURRENT_VIEW'},404)"
$count=([regex]::Matches($text,[regex]::Escape($old))).Count
if($count-ne1){throw "EXACT_ROUTE_MATCH_COUNT=$count"}
$updated=$text.Replace($old,$new)
$tmp=$target+'.tmnm_payload_repair.tmp'
[IO.File]::WriteAllText($tmp,$updated,(New-Object Text.UTF8Encoding($false)))
$check=[IO.File]::ReadAllText($tmp)
if($check.IndexOf($new,[StringComparison]::Ordinal)-lt0){Remove-Item -LiteralPath $tmp -Force;throw 'POST_WRITE_VERIFY_FAIL'}
Move-Item -LiteralPath $tmp -Destination $target -Force
$post=Get-Sha256 $target
$result=@(
'STATUS=PASS',
"PRE_SHA256=$pre",
"POST_SHA256=$post",
'EXACT_CHANGE=POST /api/workflow/payload acquisition only: CACHE.get(pid) -> resolve_canonical_package(pid, allow_cache=True)',
'SOURCE_MUTATION=1',
'PROCESS_STOP=0','PROCESS_START=0','APPROVAL_ACTION=0','SCHEDULE_ACTION=0','PUBLISHER_INVOCATION=0','FACEBOOK_WRITE=0','META_CALL=0','DESKTOP_OUTPUT=0'
)-join [Environment]::NewLine
$result|Set-Clipboard
Write-Host $result
