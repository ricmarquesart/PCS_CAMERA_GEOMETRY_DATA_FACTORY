param()
$ErrorActionPreference = 'Stop'
$PackageDir = $PSScriptRoot
$FactoryRoot = if ($env:PCS_CAMERA_FACTORY_ROOT) { $env:PCS_CAMERA_FACTORY_ROOT } else { 'C:\PCS_LABS\CAMERA_GEOMETRY_DATA_FACTORY' }
$RunRoot = Join-Path $FactoryRoot '09_RUNS\DF_G101_SCALE1K_V1_R1'
$ReturnsRoot = Join-Path $FactoryRoot '11_PACKAGES\RETURNS'
$ReturnsDir = Join-Path $ReturnsRoot 'DF_G101_SCALE1K_V1_R1'
$LogsDir = Join-Path $FactoryRoot '13_LOGS'
$IndexZip = Join-Path $ReturnsDir 'PCS_CAMERA_GEOMETRY_DATA_FACTORY_G101_SCALE1K_V1_RETURN_INDEX.zip'
$FailureZip = Join-Path $ReturnsDir 'PCS_CAMERA_GEOMETRY_DATA_FACTORY_G101_SCALE1K_V1_FAILURE_RETURN.zip'
$SetIdentity = Join-Path $ReturnsDir 'RETURN_SET_IDENTITY.json'
$Journal = Join-Path $ReturnsDir 'DF_G101_SCALE1K_V1_RUN_JOURNAL.json'
$GuardianResult = Join-Path $ReturnsDir 'DF_G101_SCALE1K_GUARDIAN_RESULT.json'

New-Item -ItemType Directory -Force -Path $ReturnsRoot | Out-Null
New-Item -ItemType Directory -Force -Path $LogsDir | Out-Null

# R2 recovery firewall. This package requires the exact existing R1 fail-closed run-root.
# Never delete/reset/rename/recreate or manually edit the run-root.
New-Item -ItemType Directory -Force -Path $ReturnsDir | Out-Null
$RecoveryMarker = Join-Path $RunRoot 'RECOVERY\G101_R2_SAMPLE0005_PRE_REMEDIATION'
if (-not (Test-Path $RunRoot)) {
    $Blocked = [ordered]@{
        schema = 'DF-G101-R2-LAUNCHER-GUARDIAN-RESULT-V1'
        status = 'BLOCKED_REQUIRED_R1_FAILURE_RUNROOT_MISSING'
        package_dir = $PackageDir
        factory_root = $FactoryRoot
        run_root = $RunRoot
        product_mutated = $false
        maya_product_scene_mutated = $false
        test77_accessed = $false
        training_started = $false
        scale_10k_authorized = $false
    }
    $Blocked | ConvertTo-Json -Depth 8 | Set-Content -Encoding UTF8 -LiteralPath $GuardianResult
    Write-Host 'DF-G101 R2 blocked: the exact existing R1 failure run-root is required.' -ForegroundColor Yellow
    Write-Host 'Do NOT create/reset the run-root manually.' -ForegroundColor Yellow
    exit 96
}
$items = @(Get-ChildItem -LiteralPath $RunRoot -Force -ErrorAction SilentlyContinue)
if ($items.Count -eq 0) {
    $Blocked = [ordered]@{
        schema = 'DF-G101-R2-LAUNCHER-GUARDIAN-RESULT-V1'
        status = 'BLOCKED_REQUIRED_R1_FAILURE_RUNROOT_EMPTY'
        package_dir = $PackageDir
        factory_root = $FactoryRoot
        run_root = $RunRoot
        product_mutated = $false
        maya_product_scene_mutated = $false
        test77_accessed = $false
        training_started = $false
        scale_10k_authorized = $false
    }
    $Blocked | ConvertTo-Json -Depth 8 | Set-Content -Encoding UTF8 -LiteralPath $GuardianResult
    Write-Host 'DF-G101 R2 blocked: the R1 run-root is empty, not the required failure prestate.' -ForegroundColor Yellow
    exit 96
}
if (Test-Path $RecoveryMarker) {
    $Blocked = [ordered]@{
        schema = 'DF-G101-R2-LAUNCHER-GUARDIAN-RESULT-V1'
        status = 'BLOCKED_R2_RECOVERY_ALREADY_INITIALIZED_DO_NOT_RERUN'
        package_dir = $PackageDir
        factory_root = $FactoryRoot
        run_root = $RunRoot
        recovery_marker = $RecoveryMarker
        product_mutated = $false
        maya_product_scene_mutated = $false
        test77_accessed = $false
        training_started = $false
        scale_10k_authorized = $false
    }
    $Blocked | ConvertTo-Json -Depth 8 | Set-Content -Encoding UTF8 -LiteralPath $GuardianResult
    Write-Host 'DF-G101 R2 blocked: recovery evidence already exists.' -ForegroundColor Yellow
    Write-Host 'Do NOT rerun. Return the existing PASS/FAIL evidence for adjudication.' -ForegroundColor Yellow
    exit 96
}

# Preserve any old R1 compact failure transport before R2 reuses the canonical failure filename.
if (Test-Path $FailureZip) {
    $R1Preserved = Join-Path $ReturnsDir 'PCS_CAMERA_GEOMETRY_DATA_FACTORY_G101_SCALE1K_V1_R1_FAILURE_RETURN_LOCAL_PRESERVED.zip'
    if (-not (Test-Path $R1Preserved)) { Copy-Item -LiteralPath $FailureZip -Destination $R1Preserved -Force }
}
# Cleanup is limited to transport wrappers. It never touches run/chunk/sample/recovery evidence.
Remove-Item -Force -ErrorAction SilentlyContinue $IndexZip, $FailureZip, $SetIdentity, $Journal, $GuardianResult
Get-ChildItem -LiteralPath $ReturnsDir -Filter 'RETURN_SHARD_*.zip' -File -ErrorAction SilentlyContinue | Remove-Item -Force -ErrorAction SilentlyContinue

$Stamp = (Get-Date).ToUniversalTime().ToString('yyyyMMdd_HHmmss_fffffff')
$Log = Join-Path $LogsDir ("DF_G101_SCALE1K_{0}.log" -f $Stamp)
$Latest = Join-Path $LogsDir 'DF_G101_SCALE1K_LATEST.log'
$PythonExe = $null
$PythonArgs = @()
$ChildExit = 9009
$LaunchError = $null
$Started = (Get-Date).ToUniversalTime()

try {
    $python = Get-Command python.exe -ErrorAction SilentlyContinue
    if (-not $python) { $python = Get-Command python -ErrorAction SilentlyContinue }
    if ($python) {
        & $python.Source -c "import sys,numpy; print(sys.executable)" *> $null
        if ($LASTEXITCODE -eq 0) {
            $PythonExe = $python.Source
            $PythonArgs = @((Join-Path $PackageDir 'df_g101_scale1k.py'), 'run', '--factory-root', $FactoryRoot)
        }
    }
    if (-not $PythonExe) {
        $py = Get-Command py.exe -ErrorAction SilentlyContinue
        if ($py) {
            & $py.Source -3 -c "import sys,numpy; print(sys.executable)" *> $null
            if ($LASTEXITCODE -eq 0) {
                $PythonExe = $py.Source
                $PythonArgs = @('-3', (Join-Path $PackageDir 'df_g101_scale1k.py'), 'run', '--factory-root', $FactoryRoot)
            }
        }
    }
    if (-not $PythonExe) { throw 'No Python interpreter with NumPy passed the G101 runtime gate.' }

    "[$((Get-Date).ToUniversalTime().ToString('o'))] DF-G101 R2 recovery guardian start" | Tee-Object -FilePath $Latest
    "factory_root=$FactoryRoot" | Tee-Object -FilePath $Latest -Append
    "package_dir=$PackageDir" | Tee-Object -FilePath $Latest -Append
    "python=$PythonExe args=$($PythonArgs -join ' ')" | Tee-Object -FilePath $Latest -Append
    & $PythonExe @PythonArgs 2>&1 | Tee-Object -FilePath $Latest -Append
    $ChildExit = $LASTEXITCODE
} catch {
    $LaunchError = $_.Exception.Message
    "GUARDIAN EXCEPTION: $LaunchError" | Tee-Object -FilePath $Latest -Append
}

$Ended = (Get-Date).ToUniversalTime()
if (Test-Path $Latest) { Copy-Item -Force $Latest $Log }
$JournalObj = $null
if (Test-Path $Journal) {
    try { $JournalObj = Get-Content -Raw -LiteralPath $Journal | ConvertFrom-Json } catch { $JournalObj = $null }
}
$ShardFiles = @()
if (Test-Path $ReturnsDir) { $ShardFiles = @(Get-ChildItem -LiteralPath $ReturnsDir -Filter 'RETURN_SHARD_*.zip' -File -ErrorAction SilentlyContinue | Sort-Object Name) }
$AllowedJournalStatus = @('MEASUREMENT_COMPLETE_PENDING_VISUAL_REVIEW','MEASUREMENT_COMPLETE_PENDING_REVIEW')
$FreshPass = ($ChildExit -eq 0 -and (Test-Path $IndexZip) -and (Test-Path $SetIdentity) -and $JournalObj -and $AllowedJournalStatus -contains $JournalObj.status -and $JournalObj.last_event -eq 'RETURN_SET_READY' -and $ShardFiles.Count -eq 10)

if (-not $FreshPass -and -not (Test-Path $FailureZip) -and $PythonExe) {
    try {
        $FailureArgs = @()
        if ([IO.Path]::GetFileName($PythonExe).ToLowerInvariant() -eq 'py.exe') { $FailureArgs += '-3' }
        $FailureArgs += (Join-Path $PackageDir 'df_g101_scale1k.py')
        $FailureArgs += 'package-failure'
        $FailureArgs += '--factory-root'
        $FailureArgs += $FactoryRoot
        & $PythonExe @FailureArgs 2>&1 | Tee-Object -FilePath $Latest -Append
    } catch {
        "FAILURE PACKAGE ERROR: $($_.Exception.Message)" | Tee-Object -FilePath $Latest -Append
    }
}

$Result = [ordered]@{
    schema = 'DF-G101-R2-LAUNCHER-GUARDIAN-RESULT-V1'
    tool_revision = 'DF_G101_SCALE1K_V1_R1_TOOL_R2'
    status = if ($FreshPass) { 'PASS_CHILD_AND_FRESH_RETURN_SET' } else { 'FAIL_CHILD_OR_NO_FRESH_RETURN_SET' }
    package_dir = $PackageDir
    factory_root = $FactoryRoot
    run_root = $RunRoot
    progress_html = (Join-Path $RunRoot 'PROGRESS.html')
    python_executable = $PythonExe
    python_arguments = $PythonArgs
    child_exit_code = $ChildExit
    launch_error = $LaunchError
    started_utc = $Started.ToString('o')
    ended_utc = $Ended.ToString('o')
    elapsed_seconds = ($Ended - $Started).TotalSeconds
    archived_log = $Log
    latest_log = $Latest
    return_index_present = (Test-Path $IndexZip)
    return_set_identity_present = (Test-Path $SetIdentity)
    return_shard_count = $ShardFiles.Count
    return_shard_names = @($ShardFiles | ForEach-Object { $_.Name })
    failure_return_zip_present = (Test-Path $FailureZip)
    journal_present = (Test-Path $Journal)
    journal_status = if ($JournalObj) { $JournalObj.status } else { $null }
    journal_last_event = if ($JournalObj) { $JournalObj.last_event } else { $null }
    product_mutated = $false
    maya_product_scene_mutated = $false
    test77_accessed = $false
    training_started = $false
    a5_changed = $false
    scale_10k_authorized = $false
}
$Result | ConvertTo-Json -Depth 8 | Set-Content -Encoding UTF8 -LiteralPath $GuardianResult

Write-Host ''
if ($FreshPass) {
    Write-Host 'DF-G101 R2 SCALE1K MEASUREMENT COMPLETE - PENDING DRIVE / STATISTICAL / VISUAL ADJUDICATION.' -ForegroundColor Green
    Write-Host 'Return the INDEX ZIP:' -ForegroundColor Green
    Write-Host $IndexZip -ForegroundColor Green
    Write-Host 'Return all ten RETURN_SHARD_*.zip files from:' -ForegroundColor Green
    Write-Host $ReturnsDir -ForegroundColor Green
    Write-Host 'Do not rerun this package.' -ForegroundColor Green
    exit 0
}
Write-Host 'DF-G101 R2 failed closed. Preserve all evidence and do not rerun/reset before adjudication.' -ForegroundColor Yellow
if (Test-Path $FailureZip) { Write-Host 'Return failure ZIP:' -ForegroundColor Yellow; Write-Host $FailureZip -ForegroundColor Yellow }
Write-Host 'Guardian result:' -ForegroundColor Yellow
Write-Host $GuardianResult -ForegroundColor Yellow
$ExitCode = if ($ChildExit -ne 0) { $ChildExit } else { 2 }
exit $ExitCode
