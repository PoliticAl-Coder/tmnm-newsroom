param([string]$TestRoot='')
$ErrorActionPreference='Stop'
$Base = if($TestRoot){$TestRoot}else{$env:LOCALAPPDATA}
$Out=Join-Path $Base 'TMNM\LocalWorker\evidence\TMNM_1_1_EXACT_SOURCE_ACQUISITION'
$Zip=Join-Path $Base 'TMNM\LocalWorker\evidence\TMNM_1_1_EXACT_SOURCE_ACQUISITION_RESULT.zip'
if(Test-Path $Out){Remove-Item $Out -Recurse -Force}
New-Item -ItemType Directory -Force -Path $Out | Out-Null
$manifest=New-Object System.Collections.ArrayList
function Add-Source([string]$Path,[string]$Tag){
 if(Test-Path -LiteralPath $Path -PathType Leaf){
  $h=(Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash.ToLowerInvariant()
  $dest=Join-Path $Out ($Tag+'__'+[IO.Path]::GetFileName($Path))
  Copy-Item -LiteralPath $Path -Destination $dest
  [void]$manifest.Add([pscustomobject]@{tag=$Tag;path=$Path;sha256=$h;size=(Get-Item -LiteralPath $Path).Length})
 }
}
$owner=Join-Path $Base 'TMNM\OwnerConsole\CanonicalBridgeReview_579a2cf7a4da5591'
Add-Source (Join-Path $owner 'tmnm_owner_console\app.py') 'OWNER_APP'
Add-Source (Join-Path $owner 'tmnm_owner_console\owner_workflow.py') 'OWNER_WORKFLOW'
$static=Join-Path $owner 'tmnm_owner_console\static'
if(Test-Path $static){Get-ChildItem -LiteralPath $static -File | ForEach-Object {Add-Source $_.FullName ('UI_'+$_.BaseName)}}
$roots=@((Join-Path $Base 'TMNM\LocalWorker'),(Join-Path $Base 'TMNM\OwnerConsole'))
$hits=New-Object System.Collections.ArrayList
foreach($r in $roots){if(Test-Path $r){
 Get-ChildItem -LiteralPath $r -Recurse -File -ErrorAction SilentlyContinue | Where-Object {
  $_.Length -lt 2097152 -and $_.FullName -notmatch '\\evidence\\|token|credential|dpapi|\.zip$|\.png$|\.jpg$'
 } | ForEach-Object {
  try{$txt=[IO.File]::ReadAllText($_.FullName)
   if($txt -match 'selected_publish_utc|SCHEDULED|NOT_QUEUED|schedule|scheduler|WRITE_DISABLED_MASTER_HOLD|/api/workflow/approve'){
    [void]$hits.Add($_.FullName)
   }}catch{}
 }
}}
$hits | Sort-Object -Unique | ForEach-Object {Add-Source $_ ('SCHED_'+[IO.Path]::GetFileNameWithoutExtension($_))}
$required=@('OWNER_APP','OWNER_WORKFLOW')
foreach($tag in $required){if(-not($manifest.tag -contains $tag)){throw "REQUIRED_SOURCE_MISSING:$tag"}}
if(-not(($manifest.tag | Where-Object {$_ -like 'UI_*'}).Count)){throw 'REQUIRED_SOURCE_MISSING:UI'}
if(-not(($manifest.tag | Where-Object {$_ -like 'SCHED_*'}).Count)){throw 'REQUIRED_SOURCE_MISSING:SCHEDULER'}
$manifestJson=$manifest | ConvertTo-Json -Depth 5
[IO.File]::WriteAllText((Join-Path $Out 'MANIFEST.json'),$manifestJson,(New-Object Text.UTF8Encoding($false)))
$ctx=New-Object System.Collections.ArrayList
foreach($m in $manifest){try{
 $lines=[IO.File]::ReadAllLines($m.path)
 for($i=0;$i -lt $lines.Length;$i++){if($lines[$i] -match 'REVIEW_READY|OWNER_APPROVED|selected_publish_utc|SCHEDULED|NOT_QUEUED|schedule|scheduler|WRITE_DISABLED_MASTER_HOLD|/api/workflow/approve'){
  [void]$ctx.Add(('{0}:{1}: {2}' -f $m.path,($i+1),$lines[$i]))
 }}
}catch{}}
if(-not($ctx.Count)){throw 'BINDING_CONTEXT_EMPTY'}
[IO.File]::WriteAllLines((Join-Path $Out 'BINDING_CONTEXT.txt'),[string[]]$ctx,(New-Object Text.UTF8Encoding($false)))
if(Test-Path $Zip){Remove-Item $Zip -Force}
Compress-Archive -Path (Join-Path $Out '*') -DestinationPath $Zip
$summary=@(
'STATUS=PASS_READ_ONLY_ACQUISITION',
"FILES=$($manifest.Count)",
"RESULT_ZIP=$Zip",
"RESULT_ZIP_SHA256=$((Get-FileHash -LiteralPath $Zip -Algorithm SHA256).Hash.ToLowerInvariant())",
'READ_ONLY=PASS','ONE_PASS_ACQUISITION=PASS','NO_DESKTOP_OUTPUT=PASS',
'SOURCE_MUTATION=0','PROCESS_STOP=0','PROCESS_START=0','APPROVAL_ACTION=0','SCHEDULE_ACTION=0',
'PUBLISHER_INVOCATION=0','FACEBOOK_WRITE=0','META_CALL=0'
) -join "`r`n"
Set-Clipboard -Value $summary
Write-Output $summary
