$ErrorActionPreference='Stop'
$ProgressPreference='SilentlyContinue'
Write-Host 'MASTER877 SHIM LOGIC READ-ONLY OBSERVATION STARTED'
$sw=[Diagnostics.Stopwatch]::StartNew();$limit=8
$shim='C:\Users\USER\AppData\Local\TMNM\OwnerConsole\PythonWHost\c49ca819d0dee3bb\TMNM_8766_PYTHONW_HOST_SHIM.py'
$expected='de7d1452d51c131da18f41360958736d6d37780543a15b180f8f27ee74b8534b'
$accepted='f32061b62264cdbde1fdb85bf454ce02025b0724ca20ff6dc595ba4c2c2531ee'
$golden=Join-Path $env:LOCALAPPDATA 'TMNM\Publisher8766Golden\article_pool_publish.py'
$R=[ordered]@{schema='TMNM_MASTER877_SHIM_LOGIC_V1';status='HOLD';host_shim_path=$shim;host_shim_sha256=$null;expected_sha256=$expected;sha_match=$false;target_resolution_logic=@();direct_target_chain=@();resolved_article_path=$null;resolved_article_sha256=$null;classification='UNRESOLVED';elapsed_seconds=$null;timeout=$false;safety=[ordered]@{read_only=$true;mutation=0;approval_action=0;schedule_action=0;publisher_invocation=0;facebook_write=0;meta_invocation=0};clipboard_delivery='FAIL'}
function Hash([string]$p){(Get-FileHash -LiteralPath $p -Algorithm SHA256).Hash.ToLowerInvariant()}
function Abs([string]$s){if(!$s){return $null};$q=$s.Trim().Trim('"').Trim("'");if($q -match '^[A-Za-z]:\\' -and $q.IndexOfAny([IO.Path]::GetInvalidPathChars()) -lt 0){return $q};return $null}
try{
 Write-Host 'Stage 1/2: verifying exact shim identity...'
 if(-not(Test-Path -LiteralPath $shim -PathType Leaf)){throw 'EXACT_SHIM_NOT_FOUND'}
 $R.host_shim_sha256=Hash $shim;$R.sha_match=($R.host_shim_sha256 -eq $expected)
 if(-not $R.sha_match){throw 'EXACT_SHIM_SHA_MISMATCH'}
 $lines=Get-Content -LiteralPath $shim
 Write-Host 'Stage 2/2: extracting target-resolution text/logic...'
 $keys='runpy|exec\s*\(|open\s*\(|subprocess|argv|environ|os\.getenv|getenv\s*\(|pathlib|Path\s*\(|join\s*\(|abspath|realpath|resolve\s*\(|dirname|__file__|base64|b64decode|decode\s*\(|compile\s*\(|importlib|site\.add|sys\.path|chdir|Popen|call\s*\(|check_call|check_output|python'
 $hit=New-Object 'System.Collections.Generic.HashSet[int]'
 for($i=0;$i -lt $lines.Count;$i++){if($lines[$i] -match $keys){for($j=[math]::Max(0,$i-2);$j -le [math]::Min($lines.Count-1,$i+2);$j++){[void]$hit.Add($j)}}}
 foreach($i in ($hit|Sort-Object)){$R.target_resolution_logic += ('{0}: {1}' -f ($i+1),$lines[$i])}
 # Direct chain only when observed code contains an absolute literal path.
 $lits=New-Object System.Collections.Generic.List[string]
 foreach($line in $lines){foreach($m in [regex]::Matches($line,'"([^"]+)"|''([^'']+)''')){$v=if($m.Groups[1].Success){$m.Groups[1].Value}else{$m.Groups[2].Value};$p=Abs $v;if($p -and -not $lits.Contains($p)){[void]$lits.Add($p)}}}
 foreach($p in $lits){
   $o=[ordered]@{path=$p;exists=$false;sha256=$null}
   if(Test-Path -LiteralPath $p -PathType Leaf){$o.exists=$true;$o.sha256=Hash $p}
   $R.direct_target_chain += [pscustomobject]$o
   if($p -match '(?i)article_pool_publish\.py$' -and $o.exists){$R.resolved_article_path=$p;$R.resolved_article_sha256=$o.sha256;break}
 }
 if($R.resolved_article_path){
   if($R.resolved_article_path -ieq $golden -and $R.resolved_article_sha256 -eq $accepted){$R.classification='ACTIVE_CANONICAL';$R.status='PASS'}
   elseif($R.resolved_article_path -ine $golden){$R.classification='STAGING_GOLDEN';$R.status='PASS'}
 }
 if($sw.Elapsed.TotalSeconds -ge $limit){$R.timeout=$true}
}catch{$R.error=[ordered]@{type=$_.Exception.GetType().FullName;message=$_.Exception.Message}}
$R.elapsed_seconds=[math]::Round($sw.Elapsed.TotalSeconds,2)
$json=$R|ConvertTo-Json -Depth 10
try{Set-Clipboard -Value $json;Start-Sleep -Milliseconds 100;if((Get-Clipboard -Raw).Trim() -eq $json.Trim()){$R.clipboard_delivery='PASS'}}catch{}
$json=$R|ConvertTo-Json -Depth 10
if($R.clipboard_delivery -eq 'PASS'){Set-Clipboard -Value $json}
Write-Host $json
Write-Host 'NO_DESKTOP_OUTPUT=true'
