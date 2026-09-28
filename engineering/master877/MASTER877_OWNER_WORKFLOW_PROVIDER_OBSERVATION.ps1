$ErrorActionPreference='Stop'
$ProgressPreference='SilentlyContinue'
Write-Host 'MASTER877 OWNER_WORKFLOW PROVIDER READ-ONLY OBSERVATION STARTED'
$sw=[Diagnostics.Stopwatch]::StartNew();$limit=10
$root=Join-Path $env:LOCALAPPDATA 'TMNM\OwnerConsole\CanonicalBridgeReview_579a2cf7a4da5591'
$wf=Join-Path $root 'tmnm_owner_console\owner_workflow.py'
$golden=Join-Path $env:LOCALAPPDATA 'TMNM\Publisher8766Golden\article_pool_publish.py'
$accepted='f32061b62264cdbde1fdb85bf454ce02025b0724ca20ff6dc595ba4c2c2531ee'
$R=[ordered]@{schema='TMNM_MASTER877_OWNER_WORKFLOW_PROVIDER_V1';status='HOLD';owner_workflow_path=$wf;owner_workflow_sha256=$null;existing_control_room_provider_logic=@();server_side_publish_reference=@();live_facebook_authority=@();direct_reference_chain=@();provider_implementation_path=$null;provider_implementation_sha256=$null;publisher8766golden_classification='UNRESOLVED';elapsed_seconds=$null;timeout=$false;safety=[ordered]@{read_only=$true;mutation=0;approval_action=0;schedule_action=0;provider_invocation=0;publisher_invocation=0;facebook_write=0;meta_invocation=0};clipboard_delivery='FAIL'}
function Hash([string]$p){(Get-FileHash -LiteralPath $p -Algorithm SHA256).Hash.ToLowerInvariant()}
function InRoot([string]$p){try{$f=[IO.Path]::GetFullPath($p);$b=[IO.Path]::GetFullPath($root).TrimEnd('\')+'\';if($f.StartsWith($b,[StringComparison]::OrdinalIgnoreCase)){return $f}}catch{};return $null}
try{
 Write-Host 'Stage 1/3: reading exact owner_workflow.py...'
 if(-not(Test-Path -LiteralPath $wf -PathType Leaf)){throw 'OWNER_WORKFLOW_NOT_FOUND'}
 $R.owner_workflow_sha256=Hash $wf;$lines=Get-Content -LiteralPath $wf
 $keys='existing_control_room_provider|SERVER_SIDE_PUBLISH_REFERENCE|LIVE_FACEBOOK_AUTHORITY|8765|provider|subprocess|runpy|importlib|sys\.path|os\.path|pathlib|Path\s*\(|join\s*\(|Popen|check_output|check_call'
 $hit=New-Object 'System.Collections.Generic.HashSet[int]'
 for($i=0;$i -lt $lines.Count;$i++){if($lines[$i] -match $keys){for($j=[math]::Max(0,$i-4);$j -le [math]::Min($lines.Count-1,$i+8);$j++){[void]$hit.Add($j)}}}
 foreach($i in ($hit|Sort-Object)){
   $s=('{0}: {1}' -f ($i+1),$lines[$i])
   if($lines[$i] -match '(?i)existing_control_room_provider|provider'){$R.existing_control_room_provider_logic += $s}
   if($lines[$i] -match 'SERVER_SIDE_PUBLISH_REFERENCE'){$R.server_side_publish_reference += $s}
   if($lines[$i] -match 'LIVE_FACEBOOK_AUTHORITY'){$R.live_facebook_authority += $s}
 }
 Write-Host 'Stage 2/3: resolving deterministic direct provider references only...'
 $mods=New-Object System.Collections.Generic.List[string]
 foreach($i in ($hit|Sort-Object)){
   $line=$lines[$i]
   if($line -match '^\s*from\s+([\.A-Za-z_][\w\.]*)\s+import\s+'){$m=$matches[1];if(-not $mods.Contains($m)){[void]$mods.Add($m)}}
   elseif($line -match '^\s*import\s+([A-Za-z_][\w\.]*)'){$m=$matches[1];if(-not $mods.Contains($m)){[void]$mods.Add($m)}}
 }
 foreach($m0 in $mods){
   $m=$m0.TrimStart('.');if(!$m){continue};$rel=$m.Replace('.','\')+'.py'
   $cands=@((Join-Path $root $rel),(Join-Path (Split-Path $wf -Parent) $rel))
   foreach($c in $cands){$p=InRoot $c;if($p -and (Test-Path -LiteralPath $p -PathType Leaf)){
     $h=Hash $p;$R.direct_reference_chain += [pscustomobject]@{module=$m0;path=$p;sha256=$h}
     $txt=Get-Content -LiteralPath $p
     if(($txt -join "\n") -match '(?i)publish|provider|article_pool_publish|8765'){
       $R.provider_implementation_path=$p;$R.provider_implementation_sha256=$h
       foreach($ln in $txt){if($ln -match '([A-Za-z]:\\[^"'']*article_pool_publish\.py)'){$q=$matches[1];if(Test-Path -LiteralPath $q -PathType Leaf){$R.provider_implementation_path=$q;$R.provider_implementation_sha256=Hash $q};break}}
       break
     }
   }}
   if($R.provider_implementation_path){break}
 }
 # Also allow an absolute literal implementation path explicitly present in owner_workflow.py.
 if(-not $R.provider_implementation_path){foreach($ln in $lines){if($ln -match '([A-Za-z]:\\[^"'']*\.(?:py|json|toml|ini|cfg))'){$q=$matches[1];if(Test-Path -LiteralPath $q -PathType Leaf){$R.direct_reference_chain += [pscustomobject]@{module='literal';path=$q;sha256=(Hash $q)};if($q -match '(?i)publish|provider|article_pool_publish'){$R.provider_implementation_path=$q;$R.provider_implementation_sha256=Hash $q;break}}}}}
 Write-Host 'Stage 3/3: classifying established implementation boundary...'
 if($R.provider_implementation_path -and $R.provider_implementation_path -ieq $golden -and $R.provider_implementation_sha256 -eq $accepted){$R.publisher8766golden_classification='ACTIVE_CANONICAL';$R.status='PASS'}
 elseif($R.provider_implementation_path -and $R.provider_implementation_path -ine $golden){$R.publisher8766golden_classification='STAGING_GOLDEN';$R.status='PASS'}
 if($sw.Elapsed.TotalSeconds -ge $limit){$R.timeout=$true}
}catch{$R.error=[ordered]@{type=$_.Exception.GetType().FullName;message=$_.Exception.Message}}
$R.elapsed_seconds=[math]::Round($sw.Elapsed.TotalSeconds,2)
$json=$R|ConvertTo-Json -Depth 10
try{Set-Clipboard -Value $json;Start-Sleep -Milliseconds 100;if((Get-Clipboard -Raw).Trim() -eq $json.Trim()){$R.clipboard_delivery='PASS'}}catch{}
$json=$R|ConvertTo-Json -Depth 10;if($R.clipboard_delivery -eq 'PASS'){Set-Clipboard -Value $json}
Write-Host $json
Write-Host 'NO_DESKTOP_OUTPUT=true'
