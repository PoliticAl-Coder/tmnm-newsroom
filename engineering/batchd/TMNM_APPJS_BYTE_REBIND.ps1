$ErrorActionPreference='Stop'
$local='C:\Users\USER\AppData\Local\TMNM\OwnerConsole\CanonicalBridgeReview_579a2cf7a4da5591\tmnm_owner_console\static\app.js'
$url='http://127.0.0.1:8766/static/app.js'
$outDir=Join-Path $env:LOCALAPPDATA 'TMNM\LocalWorker\evidence'
$out=Join-Path $outDir 'TMNM_APPJS_BYTE_REBIND_RESULT.json'
Write-Host '[1/3] Reading exact local app.js...'
if(-not(Test-Path -LiteralPath $local -PathType Leaf)){throw 'LOCAL_APP_JS_NOT_FOUND'}
$lb=[IO.File]::ReadAllBytes($local)
function Get-TMNMByteSha256([byte[]]$Bytes){$Hasher=[Security.Cryptography.SHA256]::Create();try{([BitConverter]::ToString($Hasher.ComputeHash($Bytes))).Replace('-','').ToLowerInvariant()}finally{$Hasher.Dispose()}}
$lh=Get-TMNMByteSha256 -Bytes $lb
Write-Host '[2/3] Reading exact served app.js...'
$wc=New-Object Net.WebClient;try{$sb=$wc.DownloadData($url)}finally{$wc.Dispose()}
$sh=Get-TMNMByteSha256 -Bytes $sb
$m=($lh -eq $sh)
$r=[ordered]@{schema='TMNM_APPJS_BYTE_REBIND_V2';mode='READ_ONLY_EXACT_APPJS_BYTE_REBIND';status=$(if($m){'PASS'}else{'HOLD'});local_path=$local;served_url=$url;local_sha256=$lh;served_sha256=$sh;byte_match=$m;local_bytes=$lb.Length;served_bytes=$sb.Length;mutation=0;approval_action=0;schedule_action=0;publisher_invocation=0;facebook_write=0;meta_call=0;desktop_output=0}
Write-Host '[3/3] Writing LocalWorker evidence + clipboard...'
New-Item -ItemType Directory -Force -Path $outDir|Out-Null
$j=$r|ConvertTo-Json -Depth 4
([IO.File]::WriteAllText($out,$j,[Text.UTF8Encoding]::new($false)))
Set-Clipboard -Value $j
Write-Host $j
Write-Host ('RESULT_PATH='+$out)
