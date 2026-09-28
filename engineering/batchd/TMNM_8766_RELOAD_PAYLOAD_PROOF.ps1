$ErrorActionPreference='Stop'
$pkg='TMNM-20260927-ASHA-SCHEDULER-LIVE-PROOF-01'
$expected='088aa021e092c02554abbafede96c10a9bd47a1b41803353efb779ed898325be'
$root=Join-Path $env:LOCALAPPDATA 'TMNM\OwnerConsole\CanonicalBridgeReview_579a2cf7a4da5591'
$app=Join-Path $root 'tmnm_owner_console\app.py'
$base='http://127.0.0.1:8766'
$evidenceDir=Join-Path $env:LOCALAPPDATA 'TMNM\LocalWorker\evidence'
$resultPath=Join-Path $evidenceDir 'TMNM_8766_RELOAD_PAYLOAD_PROOF_RESULT.txt'
$lines=New-Object System.Collections.Generic.List[string]
function Add([string]$s){$lines.Add($s);Write-Host $s}
function Finish([string]$status){
  Add ('STATUS='+$status); Add 'APPROVAL_ACTION=0'; Add 'SCHEDULE_ACTION=0'; Add 'PUBLISHER_INVOCATION=0'; Add 'FACEBOOK_WRITE=0'; Add 'META_CALL=0'; Add 'DESKTOP_OUTPUT=0'
  New-Item -ItemType Directory -Path $evidenceDir -Force|Out-Null
  $out=($lines -join [Environment]::NewLine)+[Environment]::NewLine
  [IO.File]::WriteAllText($resultPath,$out,(New-Object Text.UTF8Encoding($false)))
  Set-Clipboard -Value $out
  Write-Host ('EVIDENCE_PATH='+$resultPath); Write-Host 'RESULT_COPIED_TO_CLIPBOARD=TRUE'
}
function Parts([string]$cmd){
  $m=[regex]::Match($cmd,'^\s*"([^"]+)"\s*(.*)$'); if($m.Success){return @($m.Groups[1].Value,$m.Groups[2].Value)}
  $m=[regex]::Match($cmd,'^\s*(\S+)\s*(.*)$'); if($m.Success){return @($m.Groups[1].Value,$m.Groups[2].Value)}
  throw '8766_COMMANDLINE_NOT_PARSEABLE'
}
try{
 if(!(Test-Path -LiteralPath $app)){throw 'APP_SOURCE_NOT_FOUND'}
 $sha=(Get-FileHash -LiteralPath $app -Algorithm SHA256).Hash.ToLowerInvariant(); Add ('APP_SHA256='+$sha); if($sha-ne$expected){throw 'APP_SHA_MISMATCH'}
 $l=Get-NetTCPConnection -LocalPort 8766 -State Listen -ErrorAction Stop|Select-Object -First 1; if(!$l){throw '8766_NOT_LISTENING'}
 $oldPid=$l.OwningProcess; $p=Get-CimInstance Win32_Process -Filter "ProcessId=$oldPid"; if(!$p){throw '8766_PROCESS_NOT_FOUND'}
 $parts=Parts ([string]$p.CommandLine); $exe=$parts[0]; $args=$parts[1]
 if(!(Test-Path -LiteralPath $exe)){throw '8766_LAUNCH_EXE_NOT_FOUND'}; if($args-notmatch'TMNM_8766_PYTHONW_HOST_SHIM\.py'){throw '8766_CANONICAL_HOST_SHIM_NOT_PROVEN'}
 Stop-Process -Id $oldPid -Force -ErrorAction Stop; Start-Sleep -Seconds 1
 if(Get-NetTCPConnection -LocalPort 8766 -State Listen -ErrorAction SilentlyContinue){throw 'OLD_8766_STILL_LISTENING'}
 $psi=New-Object Diagnostics.ProcessStartInfo; $psi.FileName=$exe; $psi.Arguments=$args; $psi.UseShellExecute=$false; $psi.CreateNoWindow=$true
 $started=[Diagnostics.Process]::Start($psi); if(!$started){throw '8766_RESTART_FAILED'}
 Add 'RELOAD=PASS'
 $health=$null; for($i=0;$i-lt30;$i++){Start-Sleep -Seconds 1;try{$health=Invoke-WebRequest -UseBasicParsing -Uri ($base+'/api/health') -Method GET -TimeoutSec 5;if([int]$health.StatusCode-eq200){break}}catch{$health=$null}}
 if(!$health-or[int]$health.StatusCode-ne200){throw '8766_HEALTH_NOT_200'}; Add ('HEALTH_HTTP='+$health.StatusCode)
 $sha2=(Get-FileHash -LiteralPath $app -Algorithm SHA256).Hash.ToLowerInvariant(); Add ('APP_SHA256_POST_RELOAD='+$sha2); if($sha2-ne$expected){throw 'APP_SHA_CHANGED_AFTER_RELOAD'}
 $body=@{package_id=$pkg}|ConvertTo-Json -Compress
 $resp=Invoke-WebRequest -UseBasicParsing -Uri ($base+'/api/workflow/payload') -Method POST -ContentType 'application/json' -Body $body -TimeoutSec 30
 Add ('PAYLOAD_HTTP='+$resp.StatusCode); if([int]$resp.StatusCode-ne200){throw 'PAYLOAD_NOT_200'}
 $j=$resp.Content|ConvertFrom-Json; Add ('PAYLOAD_STATUS='+[string]$j.status); if([string]$j.status-ne'PAYLOAD_READY'){throw 'PAYLOAD_NOT_READY'}
 $payload=$j.payload; if($null-eq$payload){$payload=$j}
 $title=[bool](-not[string]::IsNullOrWhiteSpace([string]$payload.title)); $author=[bool](-not[string]::IsNullOrWhiteSpace([string]$payload.author)); $article=[bool](-not[string]::IsNullOrWhiteSpace([string]$payload.article_text))
 Add ('TITLE_PRESENT='+$title.ToString().ToLowerInvariant()); Add ('AUTHOR_PRESENT='+$author.ToString().ToLowerInvariant()); Add ('ARTICLE_TEXT_PRESENT='+$article.ToString().ToLowerInvariant())
 if(!($title-and$author-and$article)){throw 'REQUIRED_PAYLOAD_FIELD_MISSING'}
 Finish 'PASS'
}catch{Add ('FAILURE='+$_.Exception.Message);Finish 'HOLD';throw}
finally{Write-Host 'Press Enter to close.';[void](Read-Host)}
