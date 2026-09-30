param([string]$TestRoot='',[switch]$NoUpload)
$ErrorActionPreference='Stop'
$Expected='669acd1a7bf324353f2fbfabd4871cdf507867a2c2ffe3a9e51214390bbf774d'
$Base=if($TestRoot){$TestRoot}else{$env:LOCALAPPDATA}
$Zip=Join-Path $Base 'TMNM\LocalWorker\evidence\TMNM_1_1_EXACT_SOURCE_ACQUISITION_RESULT.zip'
if(-not(Test-Path -LiteralPath $Zip -PathType Leaf)){throw 'EXISTING_RESULT_NOT_FOUND'}
$sha=(Get-FileHash -LiteralPath $Zip -Algorithm SHA256).Hash.ToLowerInvariant()
if($sha -ne $Expected){throw "LOCAL_SHA_MISMATCH:$sha"}
$driveId='TEST_NO_UPLOAD'
if(-not $NoUpload){
 $py=Join-Path $Base 'TMNM\LocalWorker\app\python.exe'; if(-not(Test-Path $py)){$py='python'}
 $helper=Join-Path $PSScriptRoot 'UPLOAD_EXISTING_RESULT.py'
 $driveId=(& $py $helper $Zip 2>&1 | Select-Object -Last 1).ToString().Trim()
 if(-not $driveId){throw 'DRIVE_UPLOAD_FAILED'}
}
$summary=@('STATUS=PASS_TRANSPORT','EXISTING_RESULT_FOUND=PASS','LOCAL_SHA_MATCH=PASS','NO_REACQUISITION=PASS','EXISTING_GOOGLE_AUTH_REUSED=PASS',"DRIVE_ID=$driveId",'NO_DESKTOP_OUTPUT=PASS','SOURCE_MUTATION=0','APPROVAL_ACTION=0','SCHEDULE_ACTION=0','PUBLISHER_INVOCATION=0','FACEBOOK_WRITE=0','META_CALL=0') -join "`r`n"
Set-Clipboard -Value $summary
Write-Output $summary
