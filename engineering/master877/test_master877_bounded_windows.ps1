$ErrorActionPreference='Stop'
$target='engineering/master877/MASTER877_BOUNDED_RUNTIME_CANDIDATE.ps1'
$expected='31651524f30cab50a598895f1748836b8f199a034cc4b4e4a4d8143c9dd3465a'
$actual=(Get-FileHash -LiteralPath $target -Algorithm SHA256).Hash.ToLowerInvariant()
if($actual -ne $expected){throw "BOUNDED_HASH_MISMATCH actual=$actual"}
$tokens=$null;$errors=$null
[void][System.Management.Automation.Language.Parser]::ParseFile((Resolve-Path $target).Path,[ref]$tokens,[ref]$errors)
if(@($errors).Count -ne 0){$errors|%{Write-Error ("line={0} col={1} {2}" -f $_.Extent.StartLineNumber,$_.Extent.StartColumnNumber,$_.Message)};throw "BOUNDED_PARSER_FAIL count=$(@($errors).Count)"}
"BOUNDED_PARSER_PASS=true";"BOUNDED_TESTED_PS1_SHA256=$actual";"POWERSHELL_VERSION=$($PSVersionTable.PSVersion)";"PARSER_ASSEMBLY_VERSION=$([System.Management.Automation.Language.Parser].Assembly.GetName().Version)"
$fake=Join-Path $env:RUNNER_TEMP 'MASTER877 Runtime Test';New-Item -ItemType Directory -Force -Path (Join-Path $fake 'TMNM')|Out-Null
1..80|%{$d=Join-Path $fake ('TMNM\d'+$_);New-Item -ItemType Directory -Force -Path $d|Out-Null;1..80|%{Set-Content -LiteralPath (Join-Path $d ("f$_.txt")) -Value 'bounded runtime test'}}
$old=$env:USERPROFILE;$env:USERPROFILE=$fake
$psi=New-Object Diagnostics.ProcessStartInfo;$psi.FileName='powershell.exe';$psi.Arguments=('-NoProfile -ExecutionPolicy Bypass -File "'+(Resolve-Path $target).Path+'"');$psi.UseShellExecute=$false;$psi.RedirectStandardOutput=$true;$psi.RedirectStandardError=$true;$psi.CreateNoWindow=$true
$p=New-Object Diagnostics.Process;$p.StartInfo=$psi;$sw=[Diagnostics.Stopwatch]::StartNew();[void]$p.Start();$first=$p.StandardOutput.ReadLine();$firstMs=$sw.ElapsedMilliseconds
if($first -ne 'MASTER877 READ-ONLY CHECK STARTED'){throw "IMMEDIATE_OUTPUT_FAIL first=$first"};if($firstMs -gt 3000){throw "IMMEDIATE_OUTPUT_TOO_SLOW ms=$firstMs"}
if(-not $p.WaitForExit(45000)){try{$p.Kill()}catch{};throw 'BOUNDED_RUNTIME_FAIL exceeded=45s'}
$rest=$p.StandardOutput.ReadToEnd();$err=$p.StandardError.ReadToEnd();$elapsed=$sw.Elapsed.TotalSeconds;$env:USERPROFILE=$old
"IMMEDIATE_OUTPUT_PASS_MS=$firstMs";"BOUNDED_RUNTIME_SECONDS=$([Math]::Round($elapsed,2))";"BOUNDED_RUNTIME_EXIT=$($p.ExitCode)"
if($elapsed -gt 45){throw 'BOUNDED_RUNTIME_LIMIT_FAIL'};if(($first+"`n"+$rest) -notmatch '"status"\s*:\s*"HOLD"'){throw 'HOLD_RESULT_NOT_EMITTED'}
'BOUNDED_RUNTIME_PASS=true'
