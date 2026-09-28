$ErrorActionPreference='Stop'
$target='C:\Users\USER\AppData\Local\TMNM\OwnerConsole\CanonicalBridgeReview_579a2cf7a4da5591\tmnm_owner_console\app.py'
Write-Host 'TMNM APP.PY ONE-FILE READ-ONLY ACQUISITION STARTED'
if(-not(Test-Path -LiteralPath $target -PathType Leaf)){throw 'EXACT_APP_PY_NOT_FOUND'}
$bytes=[IO.File]::ReadAllBytes($target)
$sha=[Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($bytes)).ToLowerInvariant()
$text=[Text.Encoding]::UTF8.GetString($bytes)
$lines=$text -split "\r?\n"
$wanted=New-Object 'System.Collections.Generic.SortedSet[int]'
$patterns=@('CACHE','provider','canonical_snapshot','/api/packages','article_text','review_state','review_ready')
for($i=0;$i -lt $lines.Count;$i++){
  $hit=$false
  foreach($p in $patterns){if($lines[$i].IndexOf($p,[StringComparison]::OrdinalIgnoreCase)-ge 0){$hit=$true;break}}
  if($hit){$a=[Math]::Max(0,$i-8);$b=[Math]::Min($lines.Count-1,$i+12);for($j=$a;$j-le$b;$j++){[void]$wanted.Add($j)}}
}
$context=foreach($j in $wanted){'{0:D5}: {1}' -f ($j+1),$lines[$j]}
$review=@($context|Where-Object{$_ -match '(?i)review_state|review_ready|provider|CACHE'})
$article=@($context|Where-Object{$_ -match '(?i)article_text|article|body|provider|CACHE'})
$result=@(
'STATUS=PASS_READ_ONLY_ONE_FILE_ACQUISITION',
'EXACT_PATH='+$target,
'FILE_SIZE='+$bytes.Length,
'CURRENT_SHA256='+$sha,
'EXACT_HYDRATION_BLOCK=BEGIN',
($context -join [Environment]::NewLine),
'EXACT_HYDRATION_BLOCK=END',
'CURRENT_REVIEW_MAPPING=BEGIN',
($review -join [Environment]::NewLine),
'CURRENT_REVIEW_MAPPING=END',
'CURRENT_ARTICLE_MAPPING=BEGIN',
($article -join [Environment]::NewLine),
'CURRENT_ARTICLE_MAPPING=END',
'READ_ONLY=true','SOURCE_MUTATION=0','PROCESS_STOP=0','PROCESS_START=0','APPROVAL_ACTION=0','SCHEDULE_ACTION=0','PUBLISHER_INVOCATION=0','FACEBOOK_WRITE=0','META_CALL=0','DESKTOP_OUTPUT=0'
) -join [Environment]::NewLine
$outDir=Join-Path $env:LOCALAPPDATA 'TMNM\LocalWorker\evidence'
[IO.Directory]::CreateDirectory($outDir)|Out-Null
$out=Join-Path $outDir 'TMNM_APP_PY_ONE_FILE_ACQUISITION_RESULT.txt'
[IO.File]::WriteAllText($out,$result,[Text.UTF8Encoding]::new($false))
Set-Clipboard -Value $result
Write-Host $result
Write-Host ('RESULT_PATH='+$out)
