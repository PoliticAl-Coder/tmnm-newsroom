$ErrorActionPreference='Stop'
$ProgressPreference='SilentlyContinue'
$R=[ordered]@{master=877;mode='READ_ONLY_FINAL_THREE_FILE_IDENTITY';status='HOLD';mutation=0;approval_action=0;schedule_action=0;publisher_invocation=0;facebook_write=0;meta_invocation=0}
function Get-TMNMFileSha256([string]$Path){(Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash.ToLowerInvariant()}
try {
  $expected=[ordered]@{
    core='0c74cc1801880fe23d76c7f086195214dde943f4a2c6b2258cdb7767b8986852'
    adapter='7fc0ad8db8154d53d9c591aec136f3fabea7ab4bfaa4d8f0f49a617f432e37f3'
    article='f32061b62264cbbde1fdb85bf454ce02025b0724ca20ff6dc595ba4c2c2531ee'
  }
  $proc=@(Get-CimInstance Win32_Process -ErrorAction SilentlyContinue | Where-Object {$_.CommandLine -and ($_.CommandLine -match '(?i)8766|article_pool_publish|tmnm_fb_publisher|meta_connect')} | ForEach-Object {[ordered]@{pid=$_.ProcessId;name=$_.Name;executable=$_.ExecutablePath;command_line=$_.CommandLine}})
  $R.process_context=$proc

  $roots=New-Object System.Collections.Generic.List[string]
  @((Join-Path $env:LOCALAPPDATA 'TMNM'),(Join-Path $env:APPDATA 'TMNM'),(Join-Path $env:USERPROFILE 'TMNM'),(Join-Path $env:USERPROFILE 'Documents\TMNM'),(Join-Path $env:USERPROFILE 'Desktop\TMNM'),(Join-Path $env:USERPROFILE 'Documents'),(Join-Path $env:USERPROFILE 'Desktop')) | ForEach-Object {if($_ -and (Test-Path -LiteralPath $_)){[void]$roots.Add($_)}}
  foreach($p in $proc){foreach($s in @($p.executable,$p.command_line)){if($s){[regex]::Matches($s,'(?i)([A-Z]:\\[^"\s]+)')|ForEach-Object{$q=$_.Groups[1].Value.Trim('"');if(Test-Path -LiteralPath $q){$d=if((Get-Item -LiteralPath $q).PSIsContainer){$q}else{Split-Path -Parent $q};if($d -and -not $roots.Contains($d)){[void]$roots.Add($d)}}}}}
  }
  $R.search_roots=@($roots)

  $all=New-Object System.Collections.Generic.List[object];$seen=@{}
  foreach($rt in $roots){Get-ChildItem -LiteralPath $rt -Recurse -File -ErrorAction SilentlyContinue|ForEach-Object{if(-not $seen.ContainsKey($_.FullName)){$seen[$_.FullName]=$true;[void]$all.Add($_)}}}

  $core=@($all|Where-Object{$_.FullName.ToLowerInvariant().EndsWith('\tmnm_fb_publisher\core.py')}|ForEach-Object{$sha=Get-TMNMFileSha256 $_.FullName;[ordered]@{path=$_.FullName;sha256=$sha;expected_sha256=$expected.core;hash_match=($sha -eq $expected.core)}})
  $adapter=@($all|Where-Object{$_.FullName.ToLowerInvariant().EndsWith('\tmnm_fb_publisher\adapter.py')}|ForEach-Object{$sha=Get-TMNMFileSha256 $_.FullName;[ordered]@{path=$_.FullName;sha256=$sha;expected_sha256=$expected.adapter;hash_match=($sha -eq $expected.adapter)}})
  $articles=@($all|Where-Object{$_.Name -ieq 'article_pool_publish.py'}|ForEach-Object{$sha=Get-TMNMFileSha256 $_.FullName;[ordered]@{path=$_.FullName;sha256=$sha;expected_sha256=$expected.article;hash_match=($sha -eq $expected.article)}})
  $R.core_candidates=$core;$R.adapter_candidates=$adapter;$R.article_candidates=$articles
  $R.core_pass=(@($core|Where-Object{$_.hash_match}).Count -ge 1)
  $R.adapter_pass=(@($adapter|Where-Object{$_.hash_match}).Count -ge 1)

  # Read-only provenance: command lines plus bounded text/config references. Never dot-source/import/execute discovered publisher files.
  $refs=New-Object System.Collections.Generic.List[object]
  foreach($p in $proc){if($p.command_line -and $p.command_line -match '(?i)article_pool_publish\.py|Publisher8766Golden'){[void]$refs.Add([ordered]@{source='PROCESS';location=('PID '+$p.pid);text=$p.command_line})}}
  $textExt=@('.ps1','.cmd','.bat','.vbs','.py','.json','.txt','.ini','.cfg','.conf','.yaml','.yml')
  foreach($f in $all){if($textExt -contains $f.Extension.ToLowerInvariant() -and $f.Length -le 5242880){try{$hits=Select-String -LiteralPath $f.FullName -Pattern 'article_pool_publish\.py|Publisher8766Golden' -CaseSensitive:$false -ErrorAction Stop | Select-Object -First 20;foreach($h in $hits){[void]$refs.Add([ordered]@{source='TEXT_REFERENCE';location=$f.FullName;line=$h.LineNumber;text=$h.Line.Trim()})}}catch{}}}
  $R.article_references=@($refs)

  $golden=@($articles|Where-Object{$_.path -match '(?i)\\Publisher8766Golden\\article_pool_publish\.py$'})
  $goldenPath=if($golden.Count -eq 1){$golden[0].path}else{$null}
  $activeGolden=$false;$otherActive=$false
  foreach($x in $refs){$t=[string]$x.text;if($goldenPath -and ($t -like ('*'+$goldenPath+'*') -or $t -match '(?i)Publisher8766Golden\\article_pool_publish\.py')){$activeGolden=$true};foreach($a in $articles){if($goldenPath -and $a.path -ne $goldenPath -and $t -like ('*'+$a.path+'*')){$otherActive=$true}}}
  if($activeGolden -and -not $otherActive){$R.publisher8766golden_classification='ACTIVE_CANONICAL'}
  elseif(-not $activeGolden -and $otherActive){$R.publisher8766golden_classification='STAGING/GOLDEN'}
  else{$R.publisher8766golden_classification='UNRESOLVED'}
  $R.classification_basis=[ordered]@{golden_path=$goldenPath;golden_referenced_by_process_or_config=$activeGolden;other_article_candidate_explicitly_referenced=$otherActive}

  # Overall PASS requires accepted core+adapter and an accepted-hash article candidate whose active provenance is evidenced; classification itself remains evidence-driven.
  $matchingArticles=@($articles|Where-Object{$_.hash_match})
  $activeAccepted=$false
  foreach($a in $matchingArticles){foreach($x in $refs){if(([string]$x.text) -like ('*'+$a.path+'*')){$activeAccepted=$true}}}
  $R.accepted_article_hash_found=($matchingArticles.Count -ge 1)
  $R.accepted_article_active_reference=$activeAccepted
  $R.status=if($R.core_pass -and $R.adapter_pass -and $R.accepted_article_hash_found -and $activeAccepted){'PASS'}else{'HOLD'}
} catch {$R.status='HOLD';$R.error=$_.Exception.ToString()}

$ev=Join-Path $env:LOCALAPPDATA 'TMNM\LocalWorker\evidence';New-Item -ItemType Directory -Force -Path $ev|Out-Null
$out=Join-Path $ev 'TMNM_MASTER877_FINAL_THREE_FILE_IDENTITY_RESULT.json'
$receiptPath=Join-Path $ev 'TMNM_MASTER877_CLIPBOARD_RECEIPT.json'
$R.result_path=$out;$R.clipboard_delivery='VERIFYING'
$pre=$R|ConvertTo-Json -Depth 40
Set-Content -LiteralPath $out -Value $pre -Encoding UTF8
$clipOK=$false;$clipError=''
try{Set-Clipboard -Value $pre;Start-Sleep -Milliseconds 150;$clipOK=((Get-Clipboard -Raw) -ceq $pre)}catch{$clipError=$_.Exception.Message}
$R.clipboard_delivery=if($clipOK){'PASS'}else{'HOLD'}
$final=$R|ConvertTo-Json -Depth 40
Set-Content -LiteralPath $out -Value $final -Encoding UTF8
$finalClipOK=$false
try{Set-Clipboard -Value $final;Start-Sleep -Milliseconds 150;$finalClipOK=((Get-Clipboard -Raw) -ceq $final)}catch{if(-not $clipError){$clipError=$_.Exception.Message}}
$receipt=[ordered]@{master=877;clipboard_delivery=if($finalClipOK){'PASS'}else{'HOLD'};clipboard_exact_match=$finalClipOK;result_path=$out;result_sha256=Get-TMNMFileSha256 $out;clipboard_error=$clipError}
$receipt|ConvertTo-Json -Depth 10|Set-Content -LiteralPath $receiptPath -Encoding UTF8
Write-Host ('CLIPBOARD_DELIVERY='+$receipt.clipboard_delivery)
Write-Host ('CLIPBOARD_RECEIPT='+$receiptPath)
Get-Content -LiteralPath $out -Raw
Write-Host '---CLIPBOARD VERIFICATION RECEIPT---'
Get-Content -LiteralPath $receiptPath -Raw
