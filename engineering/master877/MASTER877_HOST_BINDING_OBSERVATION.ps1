$ErrorActionPreference='Stop'
$ProgressPreference='SilentlyContinue'
Write-Host 'MASTER877 HOST BINDING READ-ONLY OBSERVATION STARTED'
$sw=[Diagnostics.Stopwatch]::StartNew()
$deadlineSeconds=12
$shim='C:\Users\USER\AppData\Local\TMNM\OwnerConsole\PythonWHost\c49ca819d0dee3bb\TMNM_8766_PYTHONW_HOST_SHIM.py'
$golden='C:\Users\USER\AppData\Local\TMNM\Publisher8766Golden\article_pool_publish.py'
$accepted='f32061b62264cdbde1fdb85bf454ce02025b0724ca20ff6dc595ba4c2c2531ee'
$R=[ordered]@{schema='TMNM_MASTER877_HOST_BINDING_V1';status='HOLD';classification='UNRESOLVED';host_shim_path=$shim;host_shim_sha256=$null;direct_reference_chain=@();working_directory=$null;pythonpath=$null;sys_path=@();resolved_article_path=$null;resolved_article_sha256=$null;accepted_article_sha256=$accepted;article_hash_match=$false;timeout=$false;elapsed_seconds=$null;safety=[ordered]@{read_only=$true;mutation=0;approval_action=0;schedule_action=0;publisher_invocation=0;facebook_write=0;meta_invocation=0};clipboard_delivery='FAIL'}
function Sha([string]$p){if(Test-Path -LiteralPath $p -PathType Leaf){return (Get-FileHash -LiteralPath $p -Algorithm SHA256).Hash.ToLowerInvariant()};return $null}
function ValidLiteral([string]$s){
 if([string]::IsNullOrWhiteSpace($s)){return $null};$q=$s.Trim().Trim('"').Trim("'")
 if($q -notmatch '^[A-Za-z]:\\'){return $null};if($q.IndexOfAny([IO.Path]::GetInvalidPathChars()) -ge 0){return $null};return $q
}
try{
 Write-Host 'Stage 1/3: reading proven host shim text only...'
 if(-not(Test-Path -LiteralPath $shim -PathType Leaf)){throw 'PROVEN_HOST_SHIM_NOT_FOUND'}
 $R.host_shim_sha256=Sha $shim;$body=Get-Content -LiteralPath $shim -Raw
 $paths=New-Object System.Collections.Generic.List[string]
 foreach($m in [regex]::Matches($body,'"([^"]+)"|''([^'']+)''')){
  $q=ValidLiteral $(if($m.Groups[1].Success){$m.Groups[1].Value}else{$m.Groups[2].Value})
  if($q -and -not $paths.Contains($q)){[void]$paths.Add($q)}
 }
 if($body -match '(?im)^\s*(?:os\.chdir|chdir)\s*\(\s*["'']([^"'']+)["'']'){$R.working_directory=ValidLiteral $matches[1]}
 if($body -match '(?im)(?:PYTHONPATH)["'']?\s*[,=:\]]+\s*["'']([^"'']+)["'']'){$R.pythonpath=$matches[1]}
 foreach($m in [regex]::Matches($body,'(?im)sys\.path\.(?:append|insert)\s*\([^"'']*["'']([^"'']+)["'']')){$q=ValidLiteral $m.Groups[1].Value;if($q){$R.sys_path += $q}}
 Write-Host 'Stage 2/3: following direct literal launcher/config references only...'
 $chain=New-Object System.Collections.Generic.List[object];$seen=New-Object 'System.Collections.Generic.HashSet[string]' ([StringComparer]::OrdinalIgnoreCase)
 $queue=New-Object System.Collections.Generic.Queue[string]
 foreach($q in $paths){if($q -ne $shim -and $seen.Add($q)){$queue.Enqueue($q)}}
 $depth=0
 while($queue.Count -gt 0 -and $depth -lt 8 -and $sw.Elapsed.TotalSeconds -lt $deadlineSeconds){
  $p=$queue.Dequeue();$depth++;$exists=Test-Path -LiteralPath $p -PathType Leaf;$h=if($exists){Sha $p}else{$null}
  [void]$chain.Add([pscustomobject]@{path=$p;exists=$exists;sha256=$h})
  if($p -match '(?i)article_pool_publish\.py$' -and $exists){$R.resolved_article_path=$p;$R.resolved_article_sha256=$h;break}
  if($exists -and ([IO.Path]::GetExtension($p) -in @('.py','.ps1','.cmd','.bat','.json','.ini','.cfg','.conf','.yaml','.yml'))){
   $txt=Get-Content -LiteralPath $p -Raw
   foreach($m in [regex]::Matches($txt,'"([^"]+)"|''([^'']+)''')){
    $z=ValidLiteral $(if($m.Groups[1].Success){$m.Groups[1].Value}else{$m.Groups[2].Value})
    if($z -and $seen.Add($z)){$queue.Enqueue($z)}
   }
  }
 }
 $R.direct_reference_chain=@($chain|ForEach-Object{$_})
 if($sw.Elapsed.TotalSeconds -ge $deadlineSeconds){$R.timeout=$true}
 Write-Host 'Stage 3/3: classifying observed binding...'
 if($R.resolved_article_path){
  $R.article_hash_match=($R.resolved_article_sha256 -eq $accepted)
  if($R.resolved_article_path -ieq $golden -and $R.article_hash_match){$R.classification='ACTIVE_CANONICAL';$R.status='PASS'}
  elseif($R.resolved_article_path -ine $golden){$R.classification='STAGING_GOLDEN';$R.status='PASS'}
 }
}catch{$R.error=[ordered]@{type=$_.Exception.GetType().FullName;message=$_.Exception.Message}}
$R.elapsed_seconds=[math]::Round($sw.Elapsed.TotalSeconds,2)
$json=$R|ConvertTo-Json -Depth 10
$out=Join-Path $env:USERPROFILE 'Desktop\TMNM_MASTER877_HOST_BINDING_RESULT.json'
[IO.File]::WriteAllText($out,$json,(New-Object Text.UTF8Encoding($false)))
try{Set-Clipboard -Value $json;Start-Sleep -Milliseconds 100;$clip=Get-Clipboard -Raw;if($clip.Trim() -eq $json.Trim()){$R.clipboard_delivery='PASS'}}catch{}
$json=$R|ConvertTo-Json -Depth 10
[IO.File]::WriteAllText($out,$json,(New-Object Text.UTF8Encoding($false)))
if($R.clipboard_delivery -eq 'PASS'){Set-Clipboard -Value $json}
Write-Host $json
Write-Host ('RESULT_FILE='+$out)
