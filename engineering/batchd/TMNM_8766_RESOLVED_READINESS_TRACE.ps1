$ErrorActionPreference='Stop'
$packageId='TMNM-20260927-ASHA-SCHEDULER-LIVE-PROOF-01'
$url='http://127.0.0.1:8766/api/packages/'+[uri]::EscapeDataString($packageId)
$evidenceDir=Join-Path $env:LOCALAPPDATA 'TMNM\LocalWorker\evidence'
$resultPath=Join-Path $evidenceDir 'TMNM_8766_RESOLVED_READINESS_TRACE_RESULT.txt'
$lines=New-Object System.Collections.Generic.List[string]
function Add([string]$s){$lines.Add($s);Write-Host $s}
function Present($v){if(-not[string]::IsNullOrWhiteSpace([string]$v)){'true'}else{'false'}}
function Val($o,[string]$n){if($null-ne$o -and $o.PSObject.Properties.Name -contains $n){[string]$o.$n}else{'NOT_PRESENT'}}
try{
  $r=Invoke-WebRequest -UseBasicParsing -Uri $url -Method GET -TimeoutSec 30
  if([int]$r.StatusCode-ne200){throw ('RESOLVED_GET_HTTP_'+$r.StatusCode)}
  $p=$r.Content|ConvertFrom-Json
  $img=if($p.image){$p.image}else{$null}
  $missing=if($p.PSObject.Properties.Name -contains 'readiness_missing_fields'){@($p.readiness_missing_fields)}else{@('NOT_PRESENT')}
  $bodyLoaded=if($p.PSObject.Properties.Name -contains 'canonical_article_body_loaded'){([bool]$p.canonical_article_body_loaded).ToString().ToLowerInvariant()}else{'NOT_PRESENT'}
  $reviewReady=if($p.PSObject.Properties.Name -contains 'review_ready'){([bool]$p.review_ready).ToString().ToLowerInvariant()}else{'NOT_PRESENT'}
  Add ('CANONICAL_ARTICLE_BODY_LOADED='+$bodyLoaded)
  Add ('REVIEW_READY='+$reviewReady)
  Add ('REVIEW_STATE='+(Val $p 'review_state'))
  Add ('WORKFLOW_STATUS='+(Val $p 'workflow_status'))
  Add ('PRODUCTION_STATUS='+(Val $p 'production_status'))
  Add ('DESTINATION='+(Val $p 'destination'))
  Add ('PACKAGE_ID_PRESENT='+(Present $p.package_id))
  Add ('TITLE_PRESENT='+(Present $p.title))
  Add ('AUTHOR_PRESENT='+(Present $p.author))
  Add ('ARTICLE_TEXT_PRESENT='+(Present $p.article_text))
  Add ('READINESS_MISSING_FIELDS='+($missing -join ','))
  Add ('READINESS_INPUT_PACKAGE_ID_MATCH='+(([string]$p.package_id -eq $packageId).ToString().ToLowerInvariant()))
  Add ('READINESS_INPUT_DESTINATION='+(Val $p 'destination'))
  Add ('READINESS_INPUT_WORKFLOW_STATUS='+(Val $p 'workflow_status'))
  Add ('READINESS_INPUT_TITLE_PRESENT='+(Present $p.title))
  Add ('READINESS_INPUT_AUTHOR_PRESENT='+(Present $p.author))
  Add ('READINESS_INPUT_ARTICLE_BODY_PRESENT='+(Present $p.article_text))
  Add ('READINESS_INPUT_ARTICLE_DOC_ID_PRESENT='+(Present $p.article_doc_id))
  Add ('READINESS_INPUT_IMAGE_DRIVE_ID_PRESENT='+(Present $(if($img){$img.source_drive_id}else{''})))
  Add ('READINESS_INPUT_IMAGE_SHA256_PRESENT='+(Present $(if($img){$img.source_sha256}else{''})))
  Add ('READINESS_INPUT_OK='+(if($p.PSObject.Properties.Name -contains 'ok'){([bool]$p.ok).ToString().ToLowerInvariant()}else{'NOT_PRESENT'}))
  Add ('READINESS_INPUT_HYDRATION_ERROR='+(Val $p 'hydration_error'))
  Add 'SOURCE_CHANGE=0';Add 'RESTART=0';Add 'APPROVAL_ACTION=0';Add 'SCHEDULE_ACTION=0';Add 'PUBLISHER_INVOCATION=0';Add 'FACEBOOK_WRITE=0';Add 'META_CALL=0'
  New-Item -ItemType Directory -Path $evidenceDir -Force|Out-Null
  $out=($lines -join [Environment]::NewLine)+[Environment]::NewLine
  [IO.File]::WriteAllText($resultPath,$out,(New-Object Text.UTF8Encoding($false)));Set-Clipboard -Value $out
  Write-Host ('EVIDENCE_PATH='+$resultPath);Write-Host 'RESULT_COPIED_TO_CLIPBOARD=true'
}catch{
  Add ('TRACE_FAILURE='+$_.Exception.Message)
  New-Item -ItemType Directory -Path $evidenceDir -Force|Out-Null
  $out=($lines -join [Environment]::NewLine)+[Environment]::NewLine
  [IO.File]::WriteAllText($resultPath,$out,(New-Object Text.UTF8Encoding($false)));Set-Clipboard -Value $out
  throw
}finally{Write-Host 'Press Enter to close.';[void](Read-Host)}
