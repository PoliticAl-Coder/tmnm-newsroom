$ErrorActionPreference='Stop'
$ProgressPreference='SilentlyContinue'
$R=[ordered]@{mode='READ_ONLY_8766_REVIEW_SOURCE_ACQUISITION';status='HOLD';started_utc=(Get-Date).ToUniversalTime().ToString('o');mutation=0;approval_action=0;schedule_action=0;publisher_invocation=0;facebook_write=0;meta_call=0;desktop_output=0}
function Sha([byte[]]$b){$h=[Security.Cryptography.SHA256]::Create();try{([BitConverter]::ToString($h.ComputeHash($b))).Replace('-','').ToLowerInvariant()}finally{$h.Dispose()}}
function Text([byte[]]$b){[Text.Encoding]::UTF8.GetString($b)}
function GetBytes([string]$u){$wc=New-Object Net.WebClient;try{$wc.DownloadData($u)}finally{$wc.Dispose()}}
function Snip([string]$s,[string]$needle,[int]$radius=1800){$i=$s.IndexOf($needle,[StringComparison]::OrdinalIgnoreCase);if($i -lt 0){return $null};$a=[Math]::Max(0,$i-$radius);$n=[Math]::Min($s.Length-$a,$radius*2);$s.Substring($a,$n)}
try{
 Write-Host 'TMNM 8766 READ-ONLY SOURCE ACQUISITION STARTED'
 $sw=[Diagnostics.Stopwatch]::StartNew();$deadline=35
 Write-Host '1/4 Identifying exact live 8766 process...'
 $p=@(Get-CimInstance Win32_Process -ErrorAction Stop | Where-Object {$_.CommandLine -and $_.CommandLine -match '(?i)8766|TMNM_8766_PYTHONW_HOST_SHIM|CanonicalBridgeReview'} | Select-Object ProcessId,Name,ExecutablePath,CommandLine)
 if($p.Count -lt 1){throw 'NO_8766_PROCESS_CANDIDATE'}
 $R.process_candidates=@($p|ForEach-Object{[ordered]@{pid=$_.ProcessId;name=$_.Name;executable=$_.ExecutablePath;command_line=$_.CommandLine}})
 $root=$null;$shim=$null
 foreach($x in $p){if($x.CommandLine -match '([A-Z]:\\[^\"]*TMNM_8766_PYTHONW_HOST_SHIM\.py)'){$shim=$matches[1];break}}
 if($shim -and (Test-Path -LiteralPath $shim)){
   $R.host_shim_path=$shim;$R.host_shim_sha256=(Get-FileHash -LiteralPath $shim -Algorithm SHA256).Hash.ToLowerInvariant()
   $st=Get-Content -LiteralPath $shim -Raw
   if($st -match "(?im)^\s*PROJECT\s*=\s*r?['\"]([^'\"]+)['\"]"){$root=$matches[1]}
 }
 if(-not $root){foreach($x in $p){if($x.CommandLine -match '([A-Z]:\\[^\"]*CanonicalBridgeReview_[^\\\"\s]+)'){$root=$matches[1];break}}}
 if(-not $root -or -not (Test-Path -LiteralPath $root)){throw 'EXACT_SOURCE_ROOT_NOT_RESOLVED'}
 $R.source_root=$root
 if($sw.Elapsed.TotalSeconds -gt $deadline){throw 'BOUNDED_RUNTIME_EXCEEDED'}

 Write-Host '2/4 Fetching only localhost 8766 owner page and directly referenced scripts...'
 $base='http://127.0.0.1:8766';$htmlB=GetBytes ($base+'/');$html=Text $htmlB;$R.owner_page_sha256=Sha $htmlB
 $srcs=@([regex]::Matches($html,'<script[^>]+src=["'']([^"'']+)["'']','IgnoreCase')|ForEach-Object{$_.Groups[1].Value}|Select-Object -Unique)
 $R.script_srcs=$srcs;$hits=New-Object Collections.Generic.List[object]
 foreach($src in $srcs){
   if($sw.Elapsed.TotalSeconds -gt $deadline){throw 'BOUNDED_RUNTIME_EXCEEDED'}
   if($src -match '^https?://' -and $src -notmatch '^https?://127\.0\.0\.1:8766'){continue}
   $u=if($src -match '^https?://'){$src}elseif($src.StartsWith('/')){$base+$src}else{$base+'/'+$src}
   try{$b=GetBytes $u;$t=Text $b}catch{continue}
   $signals=@();foreach($n in @('Preview / Review','Preview','Review','openPackage','ARTICLE')){if($t.IndexOf($n,[StringComparison]::OrdinalIgnoreCase)-ge 0){$signals+=$n}}
   if($signals.Count -gt 0){
     $sn=$null;foreach($n in @('Preview / Review','openPackage','Review')){$sn=Snip $t $n;if($sn){break}}
     [void]$hits.Add([ordered]@{url=$u;served_sha256=Sha $b;length=$b.Length;signals=$signals;relevant_source_block=$sn})
   }
 }
 if($hits.Count -lt 1){
   # directly associated fallback: inspect owner page itself only
   $sn=Snip $html 'Preview / Review';if(-not $sn){$sn=Snip $html 'Review'}
   if($sn){[void]$hits.Add([ordered]@{url=$base+'/';served_sha256=Sha $htmlB;length=$htmlB.Length;signals=@('Review');relevant_source_block=$sn})}
 }
 if($hits.Count -lt 1){throw 'REVIEW_IMPLEMENTATION_NOT_FOUND_IN_DIRECTLY_SERVED_PAGE_OR_SCRIPTS'}
 $R.served_review_candidates=@($hits)

 Write-Host '3/4 Binding served bytes to the exact local project source...'
 $local=New-Object Collections.Generic.List[object]
 $files=@(Get-ChildItem -LiteralPath $root -Recurse -File -ErrorAction SilentlyContinue | Where-Object {$_.Extension -in @('.js','.html','.py')} | Select-Object -First 400)
 foreach($f in $files){
   if($sw.Elapsed.TotalSeconds -gt $deadline){throw 'BOUNDED_RUNTIME_EXCEEDED'}
   try{$fh=(Get-FileHash -LiteralPath $f.FullName -Algorithm SHA256).Hash.ToLowerInvariant()}catch{continue}
   foreach($h in $hits){if($fh -eq $h.served_sha256){[void]$local.Add([ordered]@{path=$f.FullName;sha256=$fh;served_url=$h.url;exact_byte_match=$true})}}
 }
 $R.local_exact_matches=@($local)
 if($local.Count -lt 1){$R.status='HOLD';$R.binding='SERVED_BYTES_CAPTURED_LOCAL_PATH_NOT_EXACTLY_BOUND'}else{$R.status='PASS';$R.binding='SERVED_TO_LOCAL_EXACT_SHA256_MATCH'}

 Write-Host '4/4 Writing canonical LocalWorker evidence + clipboard...'
 $R.elapsed_seconds=[Math]::Round($sw.Elapsed.TotalSeconds,2);$R.finished_utc=(Get-Date).ToUniversalTime().ToString('o')
} catch {$R.status='HOLD';$R.error=$_.Exception.Message;$R.elapsed_seconds=[Math]::Round($sw.Elapsed.TotalSeconds,2);$R.finished_utc=(Get-Date).ToUniversalTime().ToString('o')}
$ev=Join-Path $env:LOCALAPPDATA 'TMNM\LocalWorker\evidence';New-Item -ItemType Directory -Force -Path $ev|Out-Null
$out=Join-Path $ev 'TMNM_8766_REVIEW_SOURCE_ACQUISITION_RESULT.json'
$j=$R|ConvertTo-Json -Depth 20
Set-Content -LiteralPath $out -Value $j -Encoding UTF8
try{Set-Clipboard -Value $j}catch{}
Write-Host ('STATUS='+$R.status)
Write-Host ('EVIDENCE='+$out)
Write-Host ('ELAPSED_SECONDS='+$R.elapsed_seconds)
Write-Host 'RESULT COPIED TO CLIPBOARD. READ-ONLY ACQUISITION COMPLETE.'
Write-Output $j
