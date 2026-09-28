$ErrorActionPreference='Stop'
$target='engineering/master877/MASTER877_DETERMINISTIC_PATH_CANDIDATE.ps1'
$expected='LOCK_PENDING'
$actual=(Get-FileHash -LiteralPath $target -Algorithm SHA256).Hash.ToLowerInvariant();if($actual -ne $expected){throw "DETERMINISTIC_HASH_MISMATCH actual=$actual"}
$tokens=$null;$errors=$null;[void][System.Management.Automation.Language.Parser]::ParseFile((Resolve-Path $target).Path,[ref]$tokens,[ref]$errors);if(@($errors).Count){$errors|%{Write-Error ("line={0} col={1} {2}" -f $_.Extent.StartLineNumber,$_.Extent.StartColumnNumber,$_.Message)};throw "DETERMINISTIC_PARSER_FAIL count=$(@($errors).Count)"}
# Owner-shaped Stage-2 tokenizer fixture: raw command line must never reach filesystem APIs.
$ownerCmd='"pythonw.exe" "C:\Users\USER\AppData\Local\TMNM\OwnerConsole\PythonWHost\c49ca819d0dee3bb\TMNM_8766_PYTHONW_HOST_SHIM.py"'
$tokensFound=@()
foreach($m in [regex]::Matches($ownerCmd,'"([^"]+)"|([^\s"]+)')){$v=if($m.Groups[1].Success){$m.Groups[1].Value}else{$m.Groups[2].Value};if($v -match '^[A-Za-z]:\\' -and $v.IndexOfAny([IO.Path]::GetInvalidPathChars()) -lt 0){$tokensFound+=$v}}
$expectedShim='C:\Users\USER\AppData\Local\TMNM\OwnerConsole\PythonWHost\c49ca819d0dee3bb\TMNM_8766_PYTHONW_HOST_SHIM.py'
if($tokensFound -notcontains $expectedShim){throw 'OWNER_SHAPED_QUOTED_COMMANDLINE_FIXTURE_FAIL'}
Write-Output 'OWNER_SHAPED_QUOTED_COMMANDLINE_FIXTURE_PASS=true'
Write-Output 'DETERMINISTIC_PARSER_PASS=true';Write-Output "DETERMINISTIC_TESTED_PS1_SHA256=$actual";Write-Output "POWERSHELL_VERSION=$($PSVersionTable.PSVersion)"
$fake=Join-Path $env:RUNNER_TEMP 'deterministic owner';$env:LOCALAPPDATA=$fake;$root=Join-Path $fake 'TMNM\Publisher8766Golden';New-Item -ItemType Directory -Force -Path (Join-Path $root 'tmnm_fb_publisher')|Out-Null
Set-Content -LiteralPath (Join-Path $root 'article_pool_publish.py') -Value 'fixture';Set-Content -LiteralPath (Join-Path $root 'tmnm_fb_publisher\core.py') -Value 'fixture';Set-Content -LiteralPath (Join-Path $root 'tmnm_fb_publisher\adapter.py') -Value 'fixture';Set-Content -LiteralPath (Join-Path $root 'tmnm_fb_publisher\__init__.py') -Value 'fixture'
$outFile=Join-Path $env:RUNNER_TEMP 'deterministic_stdout.txt';$errFile=Join-Path $env:RUNNER_TEMP 'deterministic_stderr.txt'
$psi=New-Object Diagnostics.ProcessStartInfo;$psi.FileName='powershell.exe';$psi.Arguments="-NoProfile -ExecutionPolicy Bypass -File `"$((Resolve-Path $target).Path)`"";$psi.UseShellExecute=$false;$psi.CreateNoWindow=$true;$psi.RedirectStandardOutput=$false;$psi.RedirectStandardError=$false
$cmd="powershell.exe -NoProfile -ExecutionPolicy Bypass -File `"$((Resolve-Path $target).Path)`" > `"$outFile`" 2> `"$errFile`""
$sw=[Diagnostics.Stopwatch]::StartNew();$p=Start-Process -FilePath 'cmd.exe' -ArgumentList '/d','/c',$cmd -PassThru -WindowStyle Hidden
$first=$null;$firstMs=$null;while($sw.ElapsedMilliseconds -lt 3000 -and -not $first){if(Test-Path $outFile){$first=(Get-Content $outFile -First 1 -ErrorAction SilentlyContinue);if($first){$firstMs=$sw.ElapsedMilliseconds;break}};Start-Sleep -Milliseconds 50}
if($first -ne 'MASTER877 READ-ONLY CHECK STARTED'){try{$p.Kill()}catch{};throw "IMMEDIATE_OUTPUT_FAIL first=$first"};if(-not $p.WaitForExit(30000)){try{$p.Kill()}catch{};throw 'DETERMINISTIC_RUNTIME_TIMEOUT'};$rest=Get-Content $outFile -Raw;$err=if(Test-Path $errFile){Get-Content $errFile -Raw}else{''};Write-Output "IMMEDIATE_OUTPUT_PASS_MS=$firstMs";Write-Output "DETERMINISTIC_RUNTIME_SECONDS=$([Math]::Round($sw.Elapsed.TotalSeconds,2))";Write-Output "DETERMINISTIC_RUNTIME_EXIT=$($p.ExitCode)";if($p.ExitCode -ne 0){throw "RUNTIME_EXIT_FAIL $err"};if($rest -notmatch 'Publisher8766Golden'){throw 'EXACT_PATH_RESULT_MISSING'};Write-Output 'DETERMINISTIC_RUNTIME_PASS=true'
