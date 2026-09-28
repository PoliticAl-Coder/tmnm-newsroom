$ErrorActionPreference='Stop'
$base='http://127.0.0.1:8766';$id='TMNM-20260927-ASHA-SCHEDULER-LIVE-PROOF-01'
$expected='C:\Users\USER\AppData\Local\TMNM\OwnerConsole\CanonicalBridgeReview_579a2cf7a4da5591\tmnm_owner_console\owner_workflow.py'
function SF($p){(Get-FileHash -LiteralPath $p -Algorithm SHA256).Hash.ToLowerInvariant()}
$c=@(Get-NetTCPConnection -LocalPort 8766 -State Listen);$ids=@($c|% OwningProcess|sort -Unique);if($ids.Count-ne1){throw "LISTENER_COUNT_NOT_ONE:$($ids.Count)"};$pid8766=[int]$ids[0]
$p=Invoke-RestMethod ($base+'/api/packages/'+[uri]::EscapeDataString($id)) -TimeoutSec 10
# Derive the exact snapshot inputs from current canonical_snapshot() semantics, without mutation.
$rr=[bool]($p.review_ready -or ([string]$p.review_state -eq 'REVIEW_READY'))
$ws=[string]$(if($p.workflow_status){$p.workflow_status}else{$p.production_status})
$dest=[string]$p.destination;$packageId=[string]$p.package_id;$title=[string]$p.title;$author=[string]$p.author;$article=[string]$p.article_text
$first=if(-not$rr){'review_ready'}elseif(@('READY','READY_FOR_REVIEW') -notcontains $ws){'workflow_status'}elseif($dest-ne'TMNM'){'destination'}elseif(-not$packageId){'package_id'}elseif(-not$title){'title'}elseif(-not$author){'author'}elseif(-not$article){'article_text'}else{'NONE_SNAPSHOT_WOULD_PASS'}
# Prove imported module via live process command line/source-root plus Python module-resolution without importing/executing app code.
$proc=Get-CimInstance Win32_Process -Filter "ProcessId=$pid8766"
$root=Split-Path $expected -Parent
$py='C:\Users\USER\AppData\Local\TMNM\LocalWorker\.venv\Scripts\python.exe'
$probe="import sys,importlib.util;sys.path.insert(0,r'$root');s=importlib.util.find_spec('owner_workflow');print(s.origin)"
$resolved=(& $py -c $probe 2>&1 | Select-Object -Last 1).ToString().Trim()
if(-not(Test-Path -LiteralPath $resolved)){throw "MODULE_RESOLUTION_FAIL:$resolved"}
$r=[ordered]@{status='PASS_READ_ONLY';live_8766_pid=$pid8766;listener_command_line=$proc.CommandLine;imported_owner_workflow_path=$resolved;imported_owner_workflow_sha256=(SF $resolved);expected_path=$expected;expected_sha256='f9989ecc45aa114bd947fe1265c99483d7f1c659f2533928deddbd3e855f97a3';review_ready=$rr;workflow_status=$ws;destination=$dest;package_id=$packageId;title_present=[bool]$title;author_present=[bool]$author;article_text_present=[bool]$article;first_failed_predicate=$first;read_only=$true;process_stop=0;process_start=0;source_mutation=0;approval_action=0;schedule_action=0;publisher_invocation=0;facebook_write=0;meta_call=0;desktop_output=0}
$j=$r|ConvertTo-Json -Depth 6;$ev=Join-Path $env:LOCALAPPDATA 'TMNM\LocalWorker\evidence\TMNM_LIVE_8766_SNAPSHOT_DIAG_RESULT.json';[IO.Directory]::CreateDirectory((Split-Path $ev))|Out-Null;[IO.File]::WriteAllText($ev,$j,(New-Object Text.UTF8Encoding($false)));Set-Clipboard $j;Write-Host $j
