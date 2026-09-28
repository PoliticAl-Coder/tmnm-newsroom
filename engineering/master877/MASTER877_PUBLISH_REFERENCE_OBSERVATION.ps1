$ErrorActionPreference='Stop'
$ProgressPreference='SilentlyContinue'
Write-Host 'MASTER877 SERVER_SIDE_PUBLISH_REFERENCE READ-ONLY OBSERVATION STARTED'
$sw=[Diagnostics.Stopwatch]::StartNew()
$wf=Join-Path $env:LOCALAPPDATA 'TMNM\OwnerConsole\CanonicalBridgeReview_579a2cf7a4da5591\tmnm_owner_console\owner_workflow.py'
$expected='c8a8cd6afabec78a9498d0f1b34457c995c11f6d031c2b56f978d1913da27785'
$R=[ordered]@{schema='TMNM_MASTER877_PUBLISH_REFERENCE_V1';owner_workflow_path=$wf;owner_workflow_sha256=$null;sha_match=$false;server_side_publish_reference=@();endpoint=$null;name=$null;associated_constants=@();elapsed_seconds=$null;safety=[ordered]@{read_only=$true;endpoint_called=0;provider_invocation=0;publisher_invocation=0;mutation=0;facebook_write=0;meta_invocation=0};clipboard_delivery='FAIL'}
try{
 if(-not(Test-Path -LiteralPath $wf -PathType Leaf)){throw 'OWNER_WORKFLOW_NOT_FOUND'}
 $R.owner_workflow_sha256=(Get-FileHash -LiteralPath $wf -Algorithm SHA256).Hash.ToLowerInvariant();$R.sha_match=($R.owner_workflow_sha256 -eq $expected)
 if(-not $R.sha_match){throw 'OWNER_WORKFLOW_SHA_MISMATCH'}
 $lines=Get-Content -LiteralPath $wf
 $start=-1
 for($i=0;$i -lt $lines.Count;$i++){if($lines[$i] -match '^\s*SERVER_SIDE_PUBLISH_REFERENCE\s*='){$start=$i;break}}
 if($start -lt 0){throw 'REFERENCE_NOT_FOUND'}
 $depth=0;$begun=$false
 for($i=$start;$i -lt [math]::Min($lines.Count,$start+40);$i++){
   $line=$lines[$i];$R.server_side_publish_reference += ('{0}: {1}' -f ($i+1),$line)
   foreach($ch in $line.ToCharArray()){if($ch -eq '{'){$depth++;$begun=$true}elseif($ch -eq '}'){$depth--}}
   if($line -match '[''"]endpoint[''"]\s*:\s*[''"]([^''"]+)[''"]'){$R.endpoint=$matches[1]}
   if($line -match '[''"]name[''"]\s*:\s*[''"]([^''"]+)[''"]'){$R.name=$matches[1]}
   if($begun -and $depth -le 0){break}
 }
 foreach($i in [math]::Max(0,$start-5)..[math]::Min($lines.Count-1,$start+12)){if($lines[$i] -match '^\s*[A-Z][A-Z0-9_]*\s*='){$R.associated_constants += ('{0}: {1}' -f ($i+1),$lines[$i])}}
}catch{$R.error=[ordered]@{type=$_.Exception.GetType().FullName;message=$_.Exception.Message}}
$R.elapsed_seconds=[math]::Round($sw.Elapsed.TotalSeconds,2)
$json=$R|ConvertTo-Json -Depth 8
try{Set-Clipboard -Value $json;Start-Sleep -Milliseconds 100;if((Get-Clipboard -Raw).Trim() -eq $json.Trim()){$R.clipboard_delivery='PASS'}}catch{}
$json=$R|ConvertTo-Json -Depth 8;if($R.clipboard_delivery -eq 'PASS'){Set-Clipboard -Value $json}
Write-Host $json
Write-Host 'NO_DESKTOP_OUTPUT=true'
