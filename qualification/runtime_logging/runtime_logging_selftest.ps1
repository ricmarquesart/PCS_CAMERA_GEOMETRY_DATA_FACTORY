Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$repo = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
$module = Join-Path $repo 'TOOLS\PCSRuntimeLogging.psm1'
$wrapper = Join-Path $repo 'TOOLS\Invoke-PCSDriveLoggedCommand.ps1'
Import-Module $module -Force

function Assert-True([bool]$Condition, [string]$Message) {
    if (-not $Condition) { throw "ASSERTION_FAILED:$Message" }
}

function Invoke-WrapperChild([string[]]$Arguments) {
    $hostExe = [System.Diagnostics.Process]::GetCurrentProcess().MainModule.FileName
    & $hostExe -NoProfile -ExecutionPolicy Bypass -File $wrapper @Arguments | Out-Host
    return [int]$LASTEXITCODE
}

$root = Join-Path ([IO.Path]::GetTempPath()) ('pcs_runtime_logging_' + [Guid]::NewGuid().ToString('N'))
New-Item -ItemType Directory -Path $root | Out-Null
try {
    $passCmd = Join-Path $root 'pass.cmd'
    [System.IO.File]::WriteAllText($passCmd, "@echo PASS_STDOUT`r`n@echo PASS_STDERR 1>&2`r`n@exit /b 0`r`n", [System.Text.UTF8Encoding]::new($false))
    $returnArtifact = Join-Path $root 'return_payload.txt'
    [System.IO.File]::WriteAllText($returnArtifact, "return-evidence`r`n", [System.Text.UTF8Encoding]::new($false))

    $common = @(
        '-GateId','PHASE3_LOGGING_SYNTHETIC',
        '-ToolId','SELFTEST_V1',
        '-CommandPath',$passCmd,
        '-LogRoot',$root,
        '-PackageSha256','0123456789abcdef',
        '-AuthorizationId','CI_SYNTHETIC_ONLY',
        '-ExpectedRunRoot','CI_TEMP_ONLY',
        '-ReturnPath',$returnArtifact
    )

    $rc1 = Invoke-WrapperChild $common
    Assert-True ($rc1 -eq 0) ('first wrapper exit=' + $rc1)
    $runs1 = @(Get-ChildItem -LiteralPath $root -Directory | Where-Object { $_.Name -like 'RUN_*' })
    Assert-True ($runs1.Count -eq 1) ('expected 1 run folder, got ' + $runs1.Count)
    $run1 = $runs1[0].FullName
    foreach ($name in @('RUN_META.json','STDOUT.log','STDERR.log','RESULT.json','RUN_MANIFEST.json','COMPLETE.marker')) {
        Assert-True (Test-Path -LiteralPath (Join-Path $run1 $name) -PathType Leaf) ('missing ' + $name)
    }
    Assert-True (Test-Path -LiteralPath (Join-Path $run1 'RETURN\return_payload.txt') -PathType Leaf) 'return artifact not copied'
    $result1 = Get-Content -LiteralPath (Join-Path $run1 'RESULT.json') -Raw | ConvertFrom-Json
    Assert-True ($result1.status -eq 'PASS') ('unexpected result status=' + $result1.status)
    Assert-True ($result1.governed_action_invoked -eq $true) 'governed action flag false'
    Assert-True ($result1.automatic_retry_authorized -eq $false) 'automatic retry flag true'
    $verify1 = Test-PcsRunManifest -RunDirectory $run1
    Assert-True ($verify1.Pass) ('manifest verification failed: ' + $verify1.Reason)

    Start-Sleep -Milliseconds 5
    $rc2 = Invoke-WrapperChild $common
    Assert-True ($rc2 -eq 0) ('second wrapper exit=' + $rc2)
    $runs2 = @(Get-ChildItem -LiteralPath $root -Directory | Where-Object { $_.Name -like 'RUN_*' } | Sort-Object Name)
    Assert-True ($runs2.Count -eq 2) ('expected 2 unique run folders, got ' + $runs2.Count)
    Assert-True ($runs2[0].Name -ne $runs2[1].Name) 'run folder was overwritten/reused'
    foreach ($r in $runs2) {
        $v = Test-PcsRunManifest -RunDirectory $r.FullName
        Assert-True ($v.Pass) ('manifest failed for ' + $r.Name + ':' + $v.Reason)
    }

    # Tampering must be detectable after COMPLETE.
    $tamperRun = $runs2[1].FullName
    Add-Content -LiteralPath (Join-Path $tamperRun 'STDOUT.log') -Value 'TAMPER'
    $tamper = Test-PcsRunManifest -RunDirectory $tamperRun
    Assert-True (-not $tamper.Pass) 'tamper was not detected'
    Assert-True ($tamper.Reason -in @('BYTE_MISMATCH','SHA256_MISMATCH')) ('unexpected tamper reason=' + $tamper.Reason)

    # Missing sink must block before the governed command is invoked.
    $missingRoot = Join-Path $root 'DOES_NOT_EXIST'
    $marker = Join-Path $root 'governed_action_marker.txt'
    $blockCmd = Join-Path $root 'must_not_run.cmd'
    $blockContent = ('@echo invoked>"{0}"' -f $marker) + "`r`n@exit /b 0`r`n"
    [System.IO.File]::WriteAllText($blockCmd, $blockContent, [System.Text.UTF8Encoding]::new($false))
    $rc3 = Invoke-WrapperChild @('-GateId','MISSING_SINK_TEST','-ToolId','SELFTEST_V1','-CommandPath',$blockCmd,'-LogRoot',$missingRoot)
    Assert-True ($rc3 -eq 4) ('missing sink wrapper exit=' + $rc3)
    Assert-True (-not (Test-Path -LiteralPath $marker)) 'governed command ran despite missing sink'

    # Default resolver must be centralized and overrideable without touching science.
    $env:PCS_RUNTIME_LOG_ROOT = $root
    try { Assert-True ((Resolve-PcsLogRoot) -eq $root) 'environment log-root override failed' }
    finally { Remove-Item Env:PCS_RUNTIME_LOG_ROOT -ErrorAction SilentlyContinue }

    Write-Host 'PCS RUNTIME LOGGING SELFTEST: PASS'
    exit 0
}
finally {
    Remove-Item -LiteralPath $root -Recurse -Force -ErrorAction SilentlyContinue
}
