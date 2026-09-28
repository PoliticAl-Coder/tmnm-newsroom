$ErrorActionPreference='Stop'
$ProgressPreference='SilentlyContinue'
$R=[ordered]@{master=877;mode='READ_ONLY_DETERMINISTIC_PATH_IDENTITY';status='HOLD';mutation=0;approval_action=0;schedule_action=0;publisher_invocation=0;facebook_write=0;meta_invocation=0}
function Get-TMNMFileSha256([string]$Path){(Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash.ToLowerInvariant()}
function Add-Candidate([System.Collections.Generic.List[object]]$List,[hashtable]$Seen,[string]$Path,[string]$Kind){if($Path -and (Test-Path -LiteralPath $Path -PathType Leaf) -and -not $Seen.ContainsKey($Path)){try{$i=Get-Item -LiteralPath $Path -ErrorAction Stop;$Seen[$Path]=$true;[void]$List.Add([pscustomobject]@{FullName=$i.FullName;Name=$i.Name;Extension=$i.Extension;Length=$i.Length;Kind=$Kind})}catch{}}}
try {
  Write-Host 'MASTER877 READ-ONLY CHECK STARTED'
  $sw=[Diagnostics.Stopwatch]::StartNew();$deadlineSeconds=20;$candidateLimit=100;$textFileLimit=20
  $expected=[ordered]@{core='0c74cc1801880fe23d76c7f086195214dde943f4a2c6b2258cdb7767b8986852';adapter='7fc0ad8db8154d53d9c591aec136f3fabea7ab4bfaa4d8f0f49a617f432e37f3';article='f32061b62264cbbde1fdb85bf454ce02025b0724ca20ff6dc595ba4c2c2531ee'}
  Write-Host 'Stage 1/4: exact Publisher8766Golden probes...'
  $goldenRoot=Join-Path $env:LOCALAPPDATA 'TMNM\Publisher8766Golden'
  $exact=[ordered]@{article=Join-Path $goldenRoot 'article_pool_publish.py';core=Join-Path $goldenRoot 'tmnm_fb_publisher\core.py';adapter=Join-Path $goldenRoot 'tmnm_fb_publisher\adapter.py';init=Join-Path $goldenRoot 'tmnm_fb_publisher\__init__.py'}
  $all=New-Object System.Collections.Generic.List[object];$seen=@{}
  foreach($k in $exact.Keys){Add-Candidate $all $seen $exact[$k] ('EXACT_'+$k.ToUpperInvariant())}
  $R.exact_probe_paths=$exact;$R.exact_probe_found_count=$all.Count

  Write-Host 'Stage 2/4: bounded 8766 process and shim provenance...'
  $proc=@();$pj=Start-Job -ScriptBlock {Get-CimInstance Win32_Process -ErrorAction SilentlyContinue | Where-Object {$_.CommandLine -and $_.CommandLine -match '(?i)8766|TMNM_8766_PYTHONW_HOST_SHIM'} | ForEach-Object {[pscustomobject]@{pid=$_.ProcessId;name=$_.Name;executable=$_.ExecutablePath;command_line=$_.CommandLine}}}
  if(Wait-Job $pj -Timeout 4){$proc=@(Receive-Job $pj)}else{$R.process_discovery_timeout=$true};Remove-Job $pj -Force -ErrorAction SilentlyContinue;$R.process_context=$proc
  $refs=New-Object System.Collections.Generic.List[object];$literalPaths=New-Object System.Collections.Generic.List[string]
  foreach($p in $proc){
    $texts=@([string]$p.command_line,[string]$p.executable)
    foreach($t in $texts){if($t){foreach($m in [regex]::Matches($t,'(?i)(?:"([A-Z]:\\[^"\r\n]+?\.(?:py|json|ini|cfg|conf|yaml|yml))"|([A-Z]:\\[^\r\n]*?\.(?:py|json|ini|cfg|conf|yaml|yml)))')){$q=if($m.Groups[1].Success){$m.Groups[1].Value}else{$m.Groups[2].Value.Trim()};if($q -and -not $literalPaths.Contains($q)){[void]$literalPaths.Add($q)}}}}
  }
  $shimPaths=@($literalPaths|Where-Object{$_ -match '(?i)TMNM_8766_PYTHONW_HOST_SHIM\.py$'})
  foreach($shim in $shimPaths){if($sw.Elapsed.TotalSeconds -ge $deadlineSeconds){break};if(Test-Path -LiteralPath $shim -PathType Leaf){[void]$refs.Add([ordered]@{source='PROCESS_SHIM';location=$shim;text=$shim});try{$body=Get-Content -LiteralPath $shim -Raw -ErrorAction Stop;foreach($m in [regex]::Matches($body,'(?i)([A-Z]:\\[^"''\r\n]+?\.(?:py|json|ini|cfg|conf|yaml|yml))')){$q=$m.Groups[1].Value.Trim();if($q -and -not $literalPaths.Contains($q)){[void]$literalPaths.Add($q)}}}catch{[void]$refs.Add([ordered]@{source='SHIM_READ_ERROR';location=$shim;text=$_.Exception.Message})}}}
  foreach($q in @($literalPaths)){if($all.Count -ge $candidateLimit -or $sw.Elapsed.TotalSeconds -ge $deadlineSeconds){break};Add-Candidate $all $seen $q 'LITERAL_PROVENANCE';$d=Split-Path -Parent $q;if($d -and $d -match '(?i)TMNM'){foreach($rel in @('article_pool_publish.py','tmnm_fb_publisher\core.py','tmnm_fb_publisher\adapter.py','tmnm_fb_publisher\__init__.py')){Add-Candidate $all $seen (Join-Path $d $rel) 'IMMEDIATE_RELATIVE'}}}
  $R.literal_provenance_paths=@($literalPaths);$R.candidate_count=$all.Count;$R.candidate_limit=$candidateLimit

  Write-Host 'Stage 3/4: hashing exact candidates...'
  $core=@($all|Where-Object{$_.FullName.ToLowerInvariant().EndsWith('\tmnm_fb_publisher\core.py')}|ForEach-Object{$sha=Get-TMNMFileSha256 $_.FullName;[ordered]@{path=$_.FullName;sha256=$sha;expected_sha256=$expected.core;hash_match=($sha -eq $expected.core);kind=$_.Kind}})
  $adapter=@($all|Where-Object{$_.FullName.ToLowerInvariant().EndsWith('\tmnm_fb_publisher\adapter.py')}|ForEach-Object{$sha=Get-TMNMFileSha256 $_.FullName;[ordered]@{path=$_.FullName;sha256=$sha;expected_sha256=$expected.adapter;hash_match=($sha -eq $expected.adapter);kind=$_.Kind}})
  $articles=@($all|Where-Object{$_.Name -ieq 'article_pool_publish.py'}|ForEach-Object{$sha=Get-TMNMFileSha256 $_.FullName;[ordered]@{path=$_.FullName;sha256=$sha;expected_sha256=$expected.article;hash_match=($sha -eq $expected.article);kind=$_.Kind}})
  $R.core_candidates=$core;$R.adapter_candidates=$adapter;$R.article_candidates=$articles;$R.core_pass=(@($core|Where-Object{$_.hash_match}).Count -ge 1);$R.adapter_pass=(@($adapter|Where-Object{$_.hash_match}).Count -ge 1);$R.accepted_article_hash_found=(@($articles|Where-Object{$_.hash_match}).Count -ge 1)

  Write-Host 'Stage 4/4: provenance classification...'
  foreach($p in $proc){if($p.command_line){[void]$refs.Add([ordered]@{source='PROCESS';location=('PID '+$p.pid);text=$p.command_line})}}
  $scanned=0;foreach($f in $all){if($scanned -ge $textFileLimit -or $sw.Elapsed.TotalSeconds -ge $deadlineSeconds){break};if($f.Extension -in @('.py','.json','.ini','.cfg','.conf','.yaml','.yml') -and $f.Length -le 1048576){$scanned++;try{$hits=Select-String -LiteralPath $f.FullName -Pattern 'article_pool_publish\.py|Publisher8766Golden|tmnm_fb_publisher' -CaseSensitive:$false -ErrorAction Stop|Select-Object -First 20;foreach($h in $hits){[void]$refs.Add([ordered]@{source='TEXT_REFERENCE';location=$f.FullName;line=$h.LineNumber;text=$h.Line.Trim()})}}catch{}}}
  $R.provenance_files_scanned=$scanned;$R.article_references=@($refs)
  $goldenPath=$exact.article;$activeGolden=$false;$otherActive=$false
  foreach($x in $refs){$t=[string]$x.text;if($t -and ($t -like ('*'+$goldenPath+'*') -or $t -match '(?i)Publisher8766Golden\\article_pool_publish\.py')){$activeGolden=$true};foreach($a in $articles){if($a.path -ne $goldenPath -and $t -and $t -like ('*'+$a.path+'*')){$otherActive=$true}}}
  if($activeGolden -and -not $otherActive){$R.publisher8766golden_classification='ACTIVE_CANONICAL'}elseif(-not $activeGolden -and $otherActive){$R.publisher8766golden_classification='STAGING_GOLDEN'}else{$R.publisher8766golden_classification='UNRESOLVED'}
  $R.classification_basis=[ordered]@{golden_path=$goldenPath;golden_referenced=$activeGolden;other_article_referenced=$otherActive}
  $R.discovery_elapsed_seconds=[Math]::Round($sw.Elapsed.TotalSeconds,2);$R.discovery_timeout=($sw.Elapsed.TotalSeconds -ge $deadlineSeconds);if($R.discovery_timeout){$R.timeout_stage='PROVENANCE'}
  $R.status=if(-not $R.discovery_timeout -and $R.core_pass -and $R.adapter_pass -and $R.accepted_article_hash_found -and $R.publisher8766golden_classification -eq 'ACTIVE_CANONICAL'){'PASS'}else{'HOLD'}
  Write-Host ('completed in '+$R.discovery_elapsed_seconds+' seconds; status='+$R.status)
} catch {$R.status='HOLD';$R.error=$_.Exception.ToString()}
$final=$R|ConvertTo-Json -Depth 40
try{Set-Clipboard -Value $final;Start-Sleep -Milliseconds 100;$R.clipboard_delivery=if((Get-Clipboard -Raw) -ceq $final){'PASS'}else{'HOLD'}}catch{$R.clipboard_delivery='HOLD'}
$R|ConvertTo-Json -Depth 40
