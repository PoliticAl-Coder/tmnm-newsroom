$ErrorActionPreference='Stop'
$ExpectedAuthSha='CD09099EC23622A7AD27CBD495EAC3D0CD7C9371330BD04981B97429973B6C9E'
$ExpectedAccount='awhistler@gmail.com'
$PackageId='TMNM-20260927-ASHA-SCHEDULER-LIVE-PROOF-01'
$ArticleId='1fkBDo3xaTodg8pfpFaUhUKKG6H6Avs_6'
$Worker=Join-Path $env:LOCALAPPDATA 'TMNM\LocalWorker'
$Py=Join-Path $Worker '.venv\Scripts\python.exe'
$Auth=Join-Path $Worker 'app\google_auth.py'
$Token=Join-Path $Worker 'secrets\google_token.dpapi'
$Client=Join-Path $Worker 'secrets\google_client.dpapi'
$EvidenceDir=Join-Path $Worker 'evidence'
$ResultFile=Join-Path $EvidenceDir 'TMNM_BATCHD_GOOGLE_REAUTH_RESULT.txt'
$Backup=Join-Path $env:TEMP ('tmnm_google_token_'+[guid]::NewGuid().ToString('N')+'.dpapi')
$R=[ordered]@{STATUS='FAIL';GOOGLE_AUTH='FAIL';ARTICLE_READ='FAIL';ARTICLE_TEXT_PRESENT='false';CANONICAL_ARTICLE_BODY_LOADED='false';SOURCE_CHANGE=0;RESTART=0;APPROVAL_ACTION=0;SCHEDULE_ACTION=0;PUBLISHER_INVOCATION=0;FACEBOOK_WRITE=0;META_CALL=0;DESKTOP_OUTPUT=0}
function Put([string]$k,[object]$v){$script:R[$k]=[string]$v}
function Emit([int]$code){New-Item -ItemType Directory -Force -Path $EvidenceDir|Out-Null;$t=(($R.GetEnumerator()|%{$_.Key+'='+$_.Value})-join "`r`n")+"`r`n";[IO.File]::WriteAllText($ResultFile,$t,[Text.UTF8Encoding]::new($false));Set-Clipboard $t;Write-Host $t;Write-Host 'Press Enter to close.';[void](Read-Host);exit $code}
try{
 foreach($p in @($Py,$Auth,$Token,$Client)){if(!(Test-Path -LiteralPath $p -PathType Leaf)){throw "MISSING_REQUIRED_PATH=$p"}}
 $sha=(Get-FileHash $Auth -Algorithm SHA256).Hash.ToUpperInvariant();Put 'GOOGLE_AUTH_SHA256' $sha
 if($sha-ne$ExpectedAuthSha){throw 'GOOGLE_AUTH_IDENTITY_MISMATCH'}
 Copy-Item $Token $Backup -Force
 $o=Join-Path $env:TEMP 'tmnm_oauth_stdout.txt';$e=Join-Path $env:TEMP 'tmnm_oauth_stderr.txt'
 $p=Start-Process $Py -ArgumentList @($Auth) -Wait -PassThru -NoNewWindow -RedirectStandardOutput $o -RedirectStandardError $e
 $stdout=Get-Content $o -Raw -ErrorAction SilentlyContinue;$stderr=Get-Content $e -Raw -ErrorAction SilentlyContinue
 Put 'OAUTH_RC' $p.ExitCode
 if($p.ExitCode-ne0 -or $stdout-notmatch [regex]::Escape($ExpectedAccount)){Copy-Item $Backup $Token -Force;throw ('OAUTH_FAILED_OR_WRONG_ACCOUNT '+$stderr)}
 Put 'GOOGLE_AUTH' 'PASS';Put 'ACCOUNT_GATE' 'PASS'
 $u='http://127.0.0.1:8765/api/package/'+[uri]::EscapeDataString($PackageId)+'?destination=TMNM'
 $r=Invoke-WebRequest -UseBasicParsing -Method Get -Uri $u -TimeoutSec 30
 if([int]$r.StatusCode-ne200){throw ('ARTICLE_READ_HTTP_'+$r.StatusCode)}
 $j=([string]$r.Content)|ConvertFrom-Json
 $text=[string]$j.article_text
 Put 'ARTICLE_READ' 'PASS';Put 'ARTICLE_TEXT_PRESENT' ((-not[string]::IsNullOrWhiteSpace($text)).ToString().ToLowerInvariant())
 if([string]::IsNullOrWhiteSpace($text)){throw 'ARTICLE_TEXT_EMPTY_AFTER_REAUTH'}
 $u2='http://127.0.0.1:8766/api/packages/'+[uri]::EscapeDataString($PackageId)
 $r2=Invoke-WebRequest -UseBasicParsing -Method Get -Uri $u2 -TimeoutSec 30
 $j2=([string]$r2.Content)|ConvertFrom-Json
 Put 'CANONICAL_ARTICLE_BODY_LOADED' (([bool]$j2.canonical_article_body_loaded).ToString().ToLowerInvariant())
 Put 'READINESS_MISSING_FIELDS' (@($j2.readiness_missing_fields)-join ',')
 Put 'REVIEW_READY' (([bool]$j2.review_ready).ToString().ToLowerInvariant())
 $R.STATUS='PASS_GOOGLE_REAUTH_ARTICLE_HYDRATION'
 Emit 0
}catch{Put 'ERROR' ($_.Exception.Message);Emit 1}
finally{if(Test-Path $Backup){Remove-Item $Backup -Force -ErrorAction SilentlyContinue};Remove-Item (Join-Path $env:TEMP 'tmnm_oauth_stdout.txt') -Force -ErrorAction SilentlyContinue;Remove-Item (Join-Path $env:TEMP 'tmnm_oauth_stderr.txt') -Force -ErrorAction SilentlyContinue}
