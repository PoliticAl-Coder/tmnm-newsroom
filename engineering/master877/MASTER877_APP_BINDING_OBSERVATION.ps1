$ErrorActionPreference='Stop'
$ProgressPreference='SilentlyContinue'
Write-Host 'MASTER877 APP BINDING READ-ONLY OBSERVATION STARTED'
$sw=[Diagnostics.Stopwatch]::StartNew();$limit=10
$root=Join-Path $env:LOCALAPPDATA 'TMNM\OwnerConsole\CanonicalBridgeReview_579a2cf7a4da5591'
$app=Join-Path $root 'tmnm_owner_console\app.py'
$golden=Join-Path $env:LOCALAPPDATA 'TMNM\Publisher8766Golden\article_pool_publish.py'
$accepted='f32061b62264cdbde1fdb85bf454ce02025b0724ca20ff6dc595ba4c2c2531ee'
$R=[ordered]@{schema='TMNM_MASTER877_APP_BINDING_V1';status='HOLD';app_path=$app;app_sha256=$null;relevant_app_logic=@();direct_reference_chain=@();handler_8766=@();target_8765=@();bridge_module=$null;bridge_path=$null;implementation_path=$null;implementation_sha256=$null;publisher8766golden_classification='UNRESOLVED';elapsed_seconds=$null;timeout=$false;safety=[ordered]@{read_only=$true;mutation=0;approval_action=0;schedule_action=0;publisher_invocation=0;facebook_write=0;meta_invocation=0};clipboard_delivery='FAIL'}
function Hash([string]$p){(Get-FileHash -LiteralPath $p -Algorithm SHA256).Hash.ToLowerInvariant()}
function InsideRoot([string]$p){try{$full=[IO.Path]::GetFullPath($p);$base=[IO.Path]::GetFullPath($root).TrimEnd('\')+'\';if($full.StartsWith($base,[StringComparison]::OrdinalIgnoreCase)){return $full}}catch{};return $null}
try{
 Write-Host 'Stage 1/3: reading exact live app.py text...'
 if(-not(Test-Path -LiteralPath $app -PathType Leaf)){throw 'PROVEN_APP_NOT_FOUND'}
 $R.app_sha256=Hash $app;$lines=Get-Content -LiteralPath $app
 $keys='publish|approval|approve|8765|CANONICAL_BRIDGE|bridge|publisher|scheduler|requests\.|urllib|http://127\.0\.0\.1'
 $hits=New-Object 'System.Collections.Generic.HashSet[int]'
 for($i=0;$i -lt $lines.Count;$i++){if($lines[$i] -match $keys){for($j=[math]::Max(0,$i-3);$j -le [math]::Min($lines.Count-1,$i+4);$j++){[void]$hits.Add($j)}}}
 foreach($i in ($hits|Sort-Object)){$s=('{0}: {1}' -f ($i+1),$lines[$i]);$R.relevant_app_logic += $s;if($lines[$i] -match '(?i)(route|publish|approve|approval)'){$R.handler_8766 += $s};if($lines[$i] -match '8765|CANONICAL_BRIDGE'){$R.target_8765 += $s}}
 Write-Host 'Stage 2/3: resolving direct publish/bridge module references only...'
 $mods=New-Object System.Collections.Generic.List[string]
 foreach($line in $lines){
  if($line -notmatch $keys){continue}
  if($line -match '^\s*from\s+([A-Za-z_][\w\.]*)\s+import\s+'){$m=$matches[1];if(-not $mods.Contains($m)){[void]$mods.Add($m)}}
  elseif($line -match '^\s*import\s+([A-Za-z_][\w\.]*)'){$m=$matches[1];if(-not $mods.Contains($m)){[void]$mods.Add($m)}}
 }
 foreach($m in $mods){
   $rel=$m.Replace('.','\')+'.py';$cands=@((Join-Path $root $rel),(Join-Path (Split-Path $app -Parent) $rel))
   foreach($c in $cands){$p=InsideRoot $c;if($p -and (Test-Path -LiteralPath $p -PathType Leaf)){
      $h=Hash $p;$R.direct_reference_chain += [pscustomobject]@{module=$m;path=$p;sha256=$h};$txt=Get-Content -LiteralPath $p
      if(($txt -join "\n") -match '(?i)article_pool_publish|publisher|publish_once|/api/publish|8765'){
        $R.bridge_module=$m;$R.bridge_path=$p;$R.implementation_path=$p;$R.implementation_sha256=$h
        # Direct literal article path only if this bridge source itself establishes it.
        foreach($ln in $txt){if($ln -match '([A-Za-z]:\\[^"'']*article_pool_publish\.py)'){$q=$matches[1];if(Test-Path -LiteralPath $q -PathType Leaf){$R.implementation_path=$q;$R.implementation_sha256=Hash $q};break}}
        break
      }
   }}
   if($R.bridge_path){break}
 }
 Write-Host 'Stage 3/3: classifying established implementation boundary...'
 if($R.implementation_path -and $R.implementation_path -ieq $golden -and $R.implementation_sha256 -eq $accepted){$R.publisher8766golden_classification='ACTIVE_CANONICAL';$R.status='PASS'}
 elseif($R.implementation_path -and $R.implementation_path -ine $golden){$R.publisher8766golden_classification='STAGING_GOLDEN';$R.status='PASS'}
 if($sw.Elapsed.TotalSeconds -ge $limit){$R.timeout=$true}
}catch{$R.error=[ordered]@{type=$_.Exception.GetType().FullName;message=$_.Exception.Message}}
$R.elapsed_seconds=[math]::Round($sw.Elapsed.TotalSeconds,2)
$json=$R|ConvertTo-Json -Depth 10
try{Set-Clipboard -Value $json;Start-Sleep -Milliseconds 100;if((Get-Clipboard -Raw).Trim() -eq $json.Trim()){$R.clipboard_delivery='PASS'}}catch{}
$json=$R|ConvertTo-Json -Depth 10;if($R.clipboard_delivery -eq 'PASS'){Set-Clipboard -Value $json}
Write-Host $json
Write-Host 'NO_DESKTOP_OUTPUT=true'
