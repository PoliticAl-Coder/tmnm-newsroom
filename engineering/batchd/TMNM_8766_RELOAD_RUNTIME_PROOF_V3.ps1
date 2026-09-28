$ErrorActionPreference='Stop'
$py='C:\Users\USER\AppData\Local\TMNM\LocalWorker\.venv\Scripts\pythonw.exe'
$shim='C:\Users\USER\AppData\Local\TMNM\OwnerConsole\PythonWHost\c49ca819d0dee3bb\TMNM_8766_PYTHONW_HOST_SHIM.py'
$ow='C:\Users\USER\AppData\Local\TMNM\OwnerConsole\CanonicalBridgeReview_579a2cf7a4da5591\tmnm_owner_console\owner_workflow.py'
$sha='f9989ecc45aa114bd947fe1265c99483d7f1c659f2533928deddbd3e855f97a3';$canary='TMNM-20260927-ASHA-SCHEDULER-LIVE-PROOF-01'
function SF($p){$h=[Security.Cryptography.SHA256]::Create();try{([BitConverter]::ToString($h.ComputeHash([IO.File]::ReadAllBytes($p)))).Replace('-','').ToLowerInvariant()}finally{$h.Dispose()}}
function L(){ $c=@(Get-NetTCPConnection -LocalPort 8766 -State Listen -ErrorAction SilentlyContinue);$ids=@($c|% OwningProcess|sort -Unique);if($ids.Count-ne1){throw "LISTENER_COUNT_NOT_ONE:$($ids.Count)"};$p=Get-CimInstance Win32_Process -Filter "ProcessId=$($ids[0])";if(-not$p){throw 'LISTENER_UNRESOLVED'};if($p.Name-ne'pythonw.exe'){throw "NAME_FAIL:$($p.Name)"};if(([string]$p.CommandLine).IndexOf($shim,[StringComparison]::OrdinalIgnoreCase)-lt0){throw 'SHIM_FAIL'};[pscustomobject]@{Pid=[int]$p.ProcessId;Name=$p.Name;Exe=$p.ExecutablePath;Cmd=$p.CommandLine}}
if((SF $ow)-ne$sha){throw 'SOURCE_SHA_FAIL'}
$b=L
Stop-Process -Id $b.Pid -Force
$dl=(Get-Date).AddSeconds(20);do{Start-Sleep -Milliseconds 250;$x=@(Get-NetTCPConnection -LocalPort 8766 -State Listen -ErrorAction SilentlyContinue)}while($x.Count-and(Get-Date)-lt$dl);if($x.Count){throw 'STOP_TIMEOUT'}
Start-Process -FilePath $py -ArgumentList "`"$shim`""
$dl=(Get-Date).AddSeconds(30);$a=$null;do{Start-Sleep -Milliseconds 500;try{$a=L}catch{$a=$null}}while(-not$a-and(Get-Date)-lt$dl);if(-not$a){throw 'RESTART_TIMEOUT'}
$hw=Invoke-WebRequest 'http://127.0.0.1:8766/api/health' -UseBasicParsing -TimeoutSec 10;if($hw.StatusCode-ne200){throw 'HEALTH_HTTP_FAIL'};$h=$hw.Content|ConvertFrom-Json;if(([string]$h.status).ToUpperInvariant()-ne'HEALTHY'){throw 'HEALTH_STATUS_FAIL'}
$pkg=Invoke-RestMethod ('http://127.0.0.1:8766/api/packages/'+[uri]::EscapeDataString($canary)) -TimeoutSec 10
$body=@{package_id=$canary}|ConvertTo-Json -Compress;$pw=Invoke-WebRequest 'http://127.0.0.1:8766/api/workflow/payload' -Method Post -ContentType 'application/json' -Body $body -UseBasicParsing -TimeoutSec 10;if($pw.StatusCode-ne200){throw 'PAYLOAD_HTTP_FAIL'};$p=$pw.Content|ConvertFrom-Json
if($p.status-ne'PAYLOAD_READY'-or-not$p.payload-or-not$p.payload_sha256){throw 'PAYLOAD_GATE_FAIL'}
if($pkg.approval_status-ne'NOT_APPROVED'-or$pkg.publishing_status-ne'NOT_QUEUED'){throw "STATE_GATE_FAIL:$($pkg.approval_status):$($pkg.publishing_status)"}
$r=[ordered]@{status='PASS';root_cause='EXECUTABLEPATH_VENV_EQUALITY_GATE_REMOVED';pre_pid=$b.Pid;pre_executable=$b.Exe;post_pid=$a.Pid;post_executable=$a.Exe;source_sha256=(SF $ow);health_http=200;health_status=$h.status;build=$h.build;payload_http=200;payload_status=$p.status;payload_present=$true;payload_sha256_present=$true;approval_status=$pkg.approval_status;publishing_status=$pkg.publishing_status;approval_action=0;schedule_action=0;publisher_invocation=0;facebook_write=0;meta_call=0;desktop_output=0}
$j=$r|ConvertTo-Json -Depth 6;$ev=Join-Path $env:LOCALAPPDATA 'TMNM\LocalWorker\evidence\TMNM_8766_RELOAD_RUNTIME_PROOF_V3_RESULT.json';[IO.Directory]::CreateDirectory((Split-Path $ev))|Out-Null;[IO.File]::WriteAllText($ev,$j,(New-Object Text.UTF8Encoding($false)));Set-Clipboard $j;Write-Host $j
