$ErrorActionPreference='Stop'
$packageId='TMNM-20260927-ASHA-SCHEDULER-LIVE-PROOF-01'
$base='http://127.0.0.1:8766'
$evidenceDir=Join-Path $env:LOCALAPPDATA 'TMNM\LocalWorker\evidence'
$resultPath=Join-Path $evidenceDir 'TMNM_8766_PAYLOAD_409_CAPTURE_RESULT.txt'
$lines=New-Object System.Collections.Generic.List[string]
function Add([string]$s){$lines.Add($s);Write-Host $s}
function BoolText($v){if($v){'true'}else{'false'}}
try{
  $body=@{package_id=$packageId}|ConvertTo-Json -Compress
  $http=0;$raw='';$json=$null
  try{
    $r=Invoke-WebRequest -UseBasicParsing -Uri ($base+'/api/workflow/payload') -Method POST -ContentType 'application/json' -Body $body -TimeoutSec 30
    $http=[int]$r.StatusCode;$raw=[string]$r.Content
  }catch [System.Net.WebException]{
    $resp=$_.Exception.Response
    if($null-eq$resp){throw}
    $http=[int]$resp.StatusCode
    $stream=$resp.GetResponseStream();$reader=New-Object IO.StreamReader($stream)
    try{$raw=$reader.ReadToEnd()}finally{$reader.Dispose();$stream.Dispose()}
  }
  Add ('PAYLOAD_HTTP='+$http)
  Add ('RESPONSE_BODY='+$raw)
  try{$json=$raw|ConvertFrom-Json}catch{}
  $reason=''
  if($null-ne$json){
    foreach($n in @('error','reason','message','detail')){
      if($json.PSObject.Properties.Name -contains $n -and -not[string]::IsNullOrWhiteSpace([string]$json.$n)){$reason=[string]$json.$n;break}
    }
  }
  Add ('ERROR_REASON='+$reason)
  $snap=$null
  if($null-ne$json){
    foreach($n in @('snapshot','canonical_snapshot','package','payload')){
      if($json.PSObject.Properties.Name -contains $n -and $null-ne$json.$n){$snap=$json.$n;break}
    }
    if($null-eq$snap){$snap=$json}
  }
  $rr='';$ws='';$dest='';$packageIdPresent=$false;$title=$false;$author=$false;$article=$false
  if($null-ne$snap){
    if($snap.PSObject.Properties.Name -contains 'review_ready'){$rr=(BoolText ([bool]$snap.review_ready))}
    if($snap.PSObject.Properties.Name -contains 'workflow_status'){$ws=[string]$snap.workflow_status}
    if($snap.PSObject.Properties.Name -contains 'destination'){$dest=[string]$snap.destination}
    $packageIdPresent=-not[string]::IsNullOrWhiteSpace([string]$snap.package_id)
    $title=-not[string]::IsNullOrWhiteSpace([string]$snap.title)
    $author=-not[string]::IsNullOrWhiteSpace([string]$snap.author)
    $article=-not[string]::IsNullOrWhiteSpace([string]$snap.article_text)
  }
  Add ('REVIEW_READY='+$rr);Add ('WORKFLOW_STATUS='+$ws);Add ('DESTINATION='+$dest)
  Add ('PACKAGE_ID_PRESENT='+(BoolText $packageIdPresent));Add ('TITLE_PRESENT='+(BoolText $title));Add ('AUTHOR_PRESENT='+(BoolText $author));Add ('ARTICLE_TEXT_PRESENT='+(BoolText $article))
  Add 'APPROVAL_ACTION=0';Add 'SCHEDULE_ACTION=0';Add 'PUBLISHER_INVOCATION=0';Add 'FACEBOOK_WRITE=0';Add 'META_CALL=0';Add 'SOURCE_CHANGE=0'
  New-Item -ItemType Directory -Path $evidenceDir -Force|Out-Null
  $out=($lines -join [Environment]::NewLine)+[Environment]::NewLine
  [IO.File]::WriteAllText($resultPath,$out,(New-Object Text.UTF8Encoding($false)))
  Set-Clipboard -Value $out
  Write-Host ('EVIDENCE_PATH='+$resultPath);Write-Host 'RESULT_COPIED_TO_CLIPBOARD=true'
}catch{
  Add ('CAPTURE_FAILURE='+$_.Exception.Message)
  New-Item -ItemType Directory -Path $evidenceDir -Force|Out-Null
  $out=($lines -join [Environment]::NewLine)+[Environment]::NewLine
  [IO.File]::WriteAllText($resultPath,$out,(New-Object Text.UTF8Encoding($false)));Set-Clipboard -Value $out
  throw
}finally{Write-Host 'Press Enter to close.';[void](Read-Host)}
