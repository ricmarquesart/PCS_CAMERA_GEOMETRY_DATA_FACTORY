param(
    [Parameter(Mandatory=$true)][string]$GateId,
    [Parameter(Mandatory=$true)][string]$ToolId,
    [Parameter(Mandatory=$true)][string]$CommandPath,
    [string[]]$CommandArgs = @(),
    [string]$LogRoot = '',
    [string]$PackageSha256 = '',
    [string]$AuthorizationId = '',
    [string]$ExpectedRunRoot = '',
    [string[]]$ReturnPath = @()
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
Import-Module (Join-Path $PSScriptRoot 'PCSRuntimeLogging.psm1') -Force

$context = $null
$governedInvoked = $false
$finalExit = 4

try {
    $context = New-PcsRunContext -GateId $GateId -ToolId $ToolId -LogRoot $LogRoot -PackageSha256 $PackageSha256 -AuthorizationId $AuthorizationId -ExpectedRunRoot $ExpectedRunRoot
    Write-Host ('PCS Drive log run: ' + $context.RunDir)

    $stdoutPath = Join-Path $context.RunDir 'STDOUT.log'
    $stderrPath = Join-Path $context.RunDir 'STDERR.log'

    if (-not (Test-Path -LiteralPath $CommandPath -PathType Leaf)) {
        [System.IO.File]::WriteAllText($stdoutPath, '', [System.Text.UTF8Encoding]::new($false))
        [System.IO.File]::WriteAllText($stderrPath, "Command not found: $CommandPath`r`n", [System.Text.UTF8Encoding]::new($false))
        Write-PcsResult -Context $context -Status BLOCKED -ExitCode 4 -Phase 'PRE_INVOKE' -Detail ('COMMAND_MISSING:' + $CommandPath) -GovernedActionInvoked $false -AutomaticRetryAuthorized $false | Out-Null
        Complete-PcsRunContext -Context $context | Out-Null
        Write-Host 'BLOCKED before governed action invocation.'
        Write-Host ('Evidence: ' + $context.RunDir)
        exit 4
    }

    # Streams are intentionally merged for live operator visibility. STDERR.log records
    # that contract explicitly; RESULT.json remains the machine authority for status.
    [System.IO.File]::WriteAllText($stderrPath, "MERGED_INTO_STDOUT.log`r`n", [System.Text.UTF8Encoding]::new($false))
    $governedInvoked = $true
    Write-Host ('Invoking exactly once: ' + $CommandPath)
    & $CommandPath @CommandArgs 2>&1 | Tee-Object -FilePath $stdoutPath
    $commandExit = if ($null -eq $LASTEXITCODE) { 0 } else { [int]$LASTEXITCODE }

    $copyErrors = @()
    foreach ($p in @($ReturnPath)) {
        if ([string]::IsNullOrWhiteSpace($p)) { continue }
        try { Copy-PcsReturnArtifact -Context $context -SourcePath $p | Out-Null }
        catch { $copyErrors += $_.Exception.Message }
    }

    if ($commandExit -eq 0 -and $copyErrors.Count -eq 0) {
        $status = 'PASS'
        $detail = 'GOVERNED_COMMAND_EXIT_0_AND_REQUIRED_RETURN_ARTIFACTS_COPIED'
        $finalExit = 0
    }
    else {
        $status = 'FAIL_CLOSED'
        $detailObj = [ordered]@{
            command_exit_code = $commandExit
            return_artifact_errors = $copyErrors
        }
        $detail = $detailObj | ConvertTo-Json -Compress -Depth 10
        $finalExit = if ($commandExit -ne 0) { $commandExit } else { 3 }
    }

    Write-PcsResult -Context $context -Status $status -ExitCode $finalExit -Phase 'POST_INVOKE' -Detail $detail -GovernedActionInvoked $true -AutomaticRetryAuthorized $false | Out-Null
    Complete-PcsRunContext -Context $context | Out-Null
    Write-Host ($status + '. Evidence: ' + $context.RunDir)
    exit $finalExit
}
catch {
    $msg = $_.Exception.GetType().FullName + ': ' + $_.Exception.Message
    if ($null -ne $context) {
        try {
            $stdoutPath = Join-Path $context.RunDir 'STDOUT.log'
            $stderrPath = Join-Path $context.RunDir 'STDERR.log'
            if (-not (Test-Path -LiteralPath $stdoutPath -PathType Leaf)) {
                [System.IO.File]::WriteAllText($stdoutPath, '', [System.Text.UTF8Encoding]::new($false))
            }
            if (-not (Test-Path -LiteralPath $stderrPath -PathType Leaf)) {
                [System.IO.File]::WriteAllText($stderrPath, $msg + "`r`n", [System.Text.UTF8Encoding]::new($false))
            }
            Write-PcsResult -Context $context -Status FAIL_CLOSED -ExitCode 4 -Phase 'WRAPPER_EXCEPTION' -Detail $msg -GovernedActionInvoked $governedInvoked -AutomaticRetryAuthorized $false | Out-Null
            Complete-PcsRunContext -Context $context | Out-Null
            Write-Host ('FAIL_CLOSED. Evidence: ' + $context.RunDir)
        } catch {
            Write-Host ('FAIL_CLOSED_LOG_FINALIZATION_ERROR: ' + $_.Exception.Message)
        }
    }
    else {
        Write-Host ('BLOCKED_BEFORE_LOG_CONTEXT: ' + $msg)
    }
    exit 4
}
