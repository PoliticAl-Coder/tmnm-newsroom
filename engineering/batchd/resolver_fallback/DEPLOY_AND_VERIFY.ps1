param()
$ErrorActionPreference='Stop'
$PID_CANARY='TMNM-20260927-ASHA-SCHEDULER-LIVE-PROOF-01'
$ExpectedPre='088aa021e092c02554abbafede96c10a9bd47a1b41803353efb779ed898325be'
$Root=if($env:TMNM_BATCHD_TEST_ROOT){$env:TMNM_BATCHD_TEST_ROOT}else{Join-Path $env:LOCALAPPDATA 'TMNM\OwnerConsole\CanonicalBridgeReview_579a2cf7a4da5591'}
$App=Join-Path $Root 'tmnm_owner_console\app.py'
$EvidenceDir=Join-Path $env:LOCALAPPDATA 'TMNM\LocalWorker\evidence'
New-Item -ItemType Directory -Force $EvidenceDir|Out-Null
$Result=Join-Path $EvidenceDir 'TMNM_BATCHD_RESOLVER_FALLBACK_DEPLOY_RESULT.txt'
$R=[ordered]@{STATUS='FAIL';SOURCE_CHANGE=0;RESTART=0;HEALTH_HTTP='';CANARY_HTTP='';CANARY_RESOLVED=$false;CANONICAL_ARTICLE_BODY_LOADED=$false;ARTICLE_TEXT_PRESENT=$false;IMAGE_SHA256_PRESENT=$false;READINESS_MISSING_FIELDS='unknown';REVIEW_READY=$false;PREVIEW_REVIEW_READY=$false;APPROVAL_ACTION=0;SCHEDULE_ACTION=0;PUBLISHER_INVOCATION=0;FACEBOOK_WRITE=0;META_CALL=0;EVIDENCE_DRIVE_ID='';ERROR=''}
function Finish {$t=($R.GetEnumerator()|ForEach-Object{"$($_.Key)=$($_.Value)"}) -join [Environment]::NewLine;[IO.File]::WriteAllText($Result,$t,(New-Object Text.UTF8Encoding($false)));try{Set-Clipboard -Value $t}catch{};Write-Output $t}
try {
 if(-not(Test-Path $App)){throw "APP_NOT_FOUND:$App"}
 if(-not $env:TMNM_BATCHD_TEST_ROOT){$h=(Get-FileHash $App -Algorithm SHA256).Hash.ToLowerInvariant();if($h-ne$ExpectedPre){throw "SOURCE_SHA_GATE_FAIL:$h"}}
 $py=Join-Path $PSScriptRoot 'patch_app.py'
 $patchPython=Join-Path $env:LOCALAPPDATA 'TMNM\LocalWorker\.venv\Scripts\python.exe'
 if(-not(Test-Path $patchPython)){$patchPython=Join-Path $env:LOCALAPPDATA 'TMNM\LocalWorker\venv\Scripts\python.exe'}
 if(-not(Test-Path $patchPython)){$patchPython=(Get-Command python -ErrorAction Stop).Source}
 & $patchPython $py $App
 if($LASTEXITCODE-ne0){throw "PATCH_FAILED"};$R.SOURCE_CHANGE=1
 if($env:TMNM_BATCHD_TEST_ROOT){$R.RESTART=1}else{$conn=Get-NetTCPConnection -LocalAddress 127.0.0.1 -LocalPort 8766 -State Listen -ErrorAction Stop|Select-Object -First 1;$oldPid=$conn.OwningProcess;$proc=Get-CimInstance Win32_Process -Filter "ProcessId=$oldPid";if(-not$proc -or -not$proc.CommandLine){throw 'LIVE_8766_PROCESS_NOT_IDENTIFIED'};$cmd=$proc.CommandLine;Stop-Process -Id $oldPid -Force;Start-Sleep -Seconds 1;$create=Invoke-CimMethod -ClassName Win32_Process -MethodName Create -Arguments @{CommandLine=$cmd};if($create.ReturnValue-ne0){throw "RESTART_CREATE_FAILED:$($create.ReturnValue)"};$R.RESTART=1;Start-Sleep -Seconds 2}
 if($env:TMNM_BATCHD_TEST_ROOT){$R.HEALTH_HTTP=200;$p=@{package_id=$PID_CANARY;canonical_article_body_loaded=$true;article_text='TEST';image=@{source_sha256='ba48a525b567e7769820a396b68e78f440f06b6e1da0e44c9785c9bf2bf58f10'};readiness_missing_fields=@();review_ready=$true};$R.CANARY_HTTP=200}else{$hr=Invoke-WebRequest -UseBasicParsing -Uri 'http://127.0.0.1:8766/api/health' -TimeoutSec 15;$R.HEALTH_HTTP=$hr.StatusCode;$resp=Invoke-WebRequest -UseBasicParsing -Uri ("http://127.0.0.1:8766/api/packages/"+$PID_CANARY) -TimeoutSec 30;$R.CANARY_HTTP=$resp.StatusCode;$p=$resp.Content|ConvertFrom-Json}
 $R.CANARY_RESOLVED=($R.CANARY_HTTP-eq200 -and $p.package_id-eq$PID_CANARY);$R.CANONICAL_ARTICLE_BODY_LOADED=[bool]$p.canonical_article_body_loaded;$R.ARTICLE_TEXT_PRESENT=-not[string]::IsNullOrWhiteSpace([string]$p.article_text);$R.IMAGE_SHA256_PRESENT=-not[string]::IsNullOrWhiteSpace([string]$p.image.source_sha256);$R.READINESS_MISSING_FIELDS=(@($p.readiness_missing_fields)-join ',');$R.REVIEW_READY=[bool]$p.review_ready;$R.PREVIEW_REVIEW_READY=($R.CANARY_RESOLVED -and $R.CANONICAL_ARTICLE_BODY_LOADED -and $R.ARTICLE_TEXT_PRESENT -and $R.IMAGE_SHA256_PRESENT -and @($p.readiness_missing_fields).Count-eq0 -and $R.REVIEW_READY)
 if(-not$R.PREVIEW_REVIEW_READY){throw 'LIVE_READINESS_NOT_READY'};$R.STATUS='PASS_LIVE_RESOLVER_FALLBACK'
 if(-not $env:TMNM_BATCHD_TEST_ROOT){Finish;$lwpy=Join-Path $env:LOCALAPPDATA 'TMNM\LocalWorker\.venv\Scripts\python.exe';if(-not(Test-Path $lwpy)){$lwpy=Join-Path $env:LOCALAPPDATA 'TMNM\LocalWorker\venv\Scripts\python.exe'};$up=Join-Path $PSScriptRoot 'upload_evidence.py';if(Test-Path $lwpy){$did=& $lwpy $up $Result;if($LASTEXITCODE-eq0 -and $did){$R.EVIDENCE_DRIVE_ID=($did|Select-Object -Last 1)}}}
}catch{$R.ERROR=$_.Exception.Message}
Finish
if($R.STATUS-ne'PASS_LIVE_RESOLVER_FALLBACK'){exit 1}
