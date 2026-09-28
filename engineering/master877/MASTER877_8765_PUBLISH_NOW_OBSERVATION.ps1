$ErrorActionPreference='Stop'
$ProgressPreference='SilentlyContinue'
Write-Host 'MASTER877 LIVE 8765 PUBLISH_NOW READ-ONLY OBSERVATION STARTED'
$sw=[Diagnostics.Stopwatch]::StartNew()
$app='C:\Users\USER\AppData\Local\TMNM\ControlRoom\control_room\app.py'
$root='C:\Users\USER\AppData\Local\TMNM\ControlRoom\control_room'
$expected='6c953eaa945a6fa980f25ac38a59cdaa3c8e6753b15ab0f96ebad862b17df0ba'
$R=[ordered]@{schema='TMNM_MASTER877_8765_PUBLISH_NOW_V1';app_path=$app;app_sha256=$null;app_sha_match=$false;publish_now_source=@();connector_or_provider_construction=@();config_reference=@();terminal_call=@();direct_implementation_reference=@();implementation_path=$null;implementation_sha256=$null;publisher8766golden_classification='UNRESOLVED';elapsed_seconds=$null;safety=[ordered]@{read_only=$true;endpoint_call=0;import_execution=0;provider_invocation=0;publisher_invocation=0;facebook_meta=0;approval=0;scheduling=0;filesystem_search=0;directory_enumeration=0;desktop_output=0};clipboard_delivery='FAIL'}
function Hash([string]$p){(Get-FileHash -LiteralPath $p -Algorithm SHA256).Hash.ToLowerInvariant()}
function InRoot([string]$p){try{$f=[IO.Path]::GetFullPath($p);$b=[IO.Path]::GetFullPath($root).TrimEnd('\')+'\';if($f.StartsWith($b,[StringComparison]::OrdinalIgnoreCase)){return $f}}catch{};return $null}
try{
 if(-not(Test-Path -LiteralPath $app -PathType Leaf)){throw 'LIVE_APP_NOT_FOUND'}
 $R.app_sha256=Hash $app;$R.app_sha_match=($R.app_sha256 -eq $expected);if(-not $R.app_sha_match){throw 'LIVE_APP_SHA_MISMATCH'}
 $lines=Get-Content -LiteralPath $app
 $route=-1;$def=-1
 for($i=0;$i -lt $lines.Count;$i++){if($lines[$i] -match '/api/publish-now'){$route=$i;for($j=$i;$j -lt [math]::Min($lines.Count,$i+8);$j++){if($lines[$j] -match '^\s*(?:async\s+)?def\s+publish_now\s*\('){$def=$j;break}};if($def -ge 0){break}}}
 if($route -lt 0 -or $def -lt 0){throw 'PUBLISH_NOW_BLOCK_NOT_FOUND'}
 $indent=([regex]::Match($lines[$def],'^\s*')).Value.Length;$end=$lines.Count-1
 for($i=$def+1;$i -lt $lines.Count;$i++){if($lines[$i].Trim() -eq ''){continue};$ind=([regex]::Match($lines[$i],'^\s*')).Value.Length;if($ind -le $indent -and $lines[$i] -match '^\s*(?:@|(?:async\s+)?def\s+|class\s+)'){$end=$i-1;break}}
 for($i=$route;$i -le $end;$i++){$R.publish_now_source += ('{0}: {1}' -f ($i+1),$lines[$i])}
 $block=($lines[$route..$end] -join "\n")
 foreach($i in $route..$end){$s=('{0}: {1}' -f ($i+1),$lines[$i])
   if($lines[$i] -match '(?i)connector|provider|publisher'){$R.connector_or_provider_construction += $s}
   if($lines[$i] -match '(?i)CFG|config|publisher_bridge'){$R.config_reference += $s}
   if($lines[$i] -match '(?i)\.publish\s*\(|\.execute\s*\(|\.invoke\s*\(|publish_once\s*\(|publish_now\s*\('){$R.terminal_call += $s}
 }
 # Identify a single directly referenced local imported symbol used in this block.
 $imports=@()
 for($i=0;$i -lt $lines.Count;$i++){
   if($lines[$i] -match '^\s*from\s+([A-Za-z_][\w\.]*)\s+import\s+(.+)$'){
     $mod=$matches[1];$names=$matches[2]
     foreach($n0 in ($names -split ',')){ $n=($n0 -replace '\s+as\s+.*$','').Trim(' ','(',')');if($n -and $block -match ('\b'+[regex]::Escape($n)+'\b')){$imports += [pscustomobject]@{module=$mod;symbol=$n;line=$i+1}}}
   } elseif($lines[$i] -match '^\s*import\s+([A-Za-z_][\w\.]*)'){$mod=$matches[1];if($block -match ('\b'+[regex]::Escape($mod.Split('.')[0])+'\b')){$imports += [pscustomobject]@{module=$mod;symbol=$mod.Split('.')[0];line=$i+1}}}
 }
 $local=@()
 foreach($x in $imports){$p=InRoot (Join-Path $root ($x.module.Replace('.','\')+'.py'));if($p -and (Test-Path -LiteralPath $p -PathType Leaf)){$local += [pscustomobject]@{module=$x.module;symbol=$x.symbol;path=$p;sha256=(Hash $p)}}}
 # Deduplicate exact paths; establish only if exactly one local implementation source is directly used.
 $uniq=@($local|Group-Object path|ForEach-Object{$_.Group[0]})
 foreach($x in $uniq){$R.direct_implementation_reference += $x}
 if($uniq.Count -eq 1){$R.implementation_path=$uniq[0].path;$R.implementation_sha256=$uniq[0].sha256}
}catch{$R.error=[ordered]@{type=$_.Exception.GetType().FullName;message=$_.Exception.Message}}
$R.elapsed_seconds=[math]::Round($sw.Elapsed.TotalSeconds,2)
$json=$R|ConvertTo-Json -Depth 10
try{Set-Clipboard -Value $json;Start-Sleep -Milliseconds 100;if((Get-Clipboard -Raw).Trim() -eq $json.Trim()){$R.clipboard_delivery='PASS'}}catch{}
$json=$R|ConvertTo-Json -Depth 10;if($R.clipboard_delivery -eq 'PASS'){Set-Clipboard -Value $json}
Write-Host $json
Write-Host 'NO_DESKTOP_OUTPUT=true'
