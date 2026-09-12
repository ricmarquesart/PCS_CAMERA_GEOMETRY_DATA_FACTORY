Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$script:DefaultDfG101LogRoot = 'G:\My Drive\PCS_RUNTIME_LOGS\CAMERA_GEOMETRY_DATA_FACTORY\DF_G101'

function Write-PcsJsonAtomic {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory=$true)][string]$Path,
        [Parameter(Mandatory=$true)]$Value
    )
    $parent = Split-Path -Parent $Path
    if (-not (Test-Path -LiteralPath $parent -PathType Container)) {
        throw "PCS_LOG_PARENT_MISSING:$parent"
    }
    $tmp = $Path + '.tmp.' + [Guid]::NewGuid().ToString('N')
    $json = $Value | ConvertTo-Json -Depth 100
    [System.IO.File]::WriteAllText($tmp, $json + "`r`n", [System.Text.UTF8Encoding]::new($false))
    Move-Item -LiteralPath $tmp -Destination $Path -Force
}

function Get-PcsFileSha256 {
    [CmdletBinding()]
    param([Parameter(Mandatory=$true)][string]$Path)
    return (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash.ToLowerInvariant()
}

function Resolve-PcsLogRoot {
    [CmdletBinding()]
    param([string]$LogRoot)
    if (-not [string]::IsNullOrWhiteSpace($LogRoot)) { return $LogRoot }
    if (-not [string]::IsNullOrWhiteSpace($env:PCS_RUNTIME_LOG_ROOT)) { return $env:PCS_RUNTIME_LOG_ROOT }
    return $script:DefaultDfG101LogRoot
}

function Assert-PcsWritableLogRoot {
    [CmdletBinding()]
    param([Parameter(Mandatory=$true)][string]$LogRoot)
    if (-not (Test-Path -LiteralPath $LogRoot -PathType Container)) {
        throw "PCS_LOG_ROOT_MISSING:$LogRoot"
    }
    $probe = Join-Path $LogRoot ('.pcs_write_probe_' + [Guid]::NewGuid().ToString('N') + '.tmp')
    try {
        [System.IO.File]::WriteAllText($probe, 'probe', [System.Text.UTF8Encoding]::new($false))
        if (-not (Test-Path -LiteralPath $probe -PathType Leaf)) {
            throw "PCS_LOG_ROOT_PROBE_NOT_VISIBLE:$LogRoot"
        }
    }
    finally {
        if (Test-Path -LiteralPath $probe -PathType Leaf) {
            Remove-Item -LiteralPath $probe -Force -ErrorAction SilentlyContinue
        }
    }
}

function ConvertTo-PcsSafeToken {
    [CmdletBinding()]
    param([Parameter(Mandatory=$true)][string]$Value)
    $v = $Value.Trim()
    if ([string]::IsNullOrWhiteSpace($v)) { throw 'PCS_LOG_EMPTY_TOKEN' }
    $v = [regex]::Replace($v, '[^A-Za-z0-9._-]+', '_')
    $v = $v.Trim('_')
    if ([string]::IsNullOrWhiteSpace($v)) { throw 'PCS_LOG_TOKEN_SANITIZED_EMPTY' }
    return $v
}

function New-PcsRunContext {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory=$true)][string]$GateId,
        [Parameter(Mandatory=$true)][string]$ToolId,
        [string]$LogRoot,
        [string]$PackageSha256 = '',
        [string]$AuthorizationId = '',
        [string]$ExpectedRunRoot = ''
    )
    $resolved = Resolve-PcsLogRoot -LogRoot $LogRoot
    Assert-PcsWritableLogRoot -LogRoot $resolved

    $gate = ConvertTo-PcsSafeToken -Value $GateId
    $tool = ConvertTo-PcsSafeToken -Value $ToolId
    $stamp = [DateTime]::UtcNow.ToString('yyyyMMddTHHmmssfffZ')
    $runId = "RUN_${stamp}__${gate}__${tool}"
    $runDir = Join-Path $resolved $runId
    if (Test-Path -LiteralPath $runDir) {
        throw "PCS_LOG_RUN_FOLDER_COLLISION:$runDir"
    }
    New-Item -ItemType Directory -Path $runDir -ErrorAction Stop | Out-Null
    New-Item -ItemType Directory -Path (Join-Path $runDir 'RETURN') -ErrorAction Stop | Out-Null

    $meta = [ordered]@{
        schema = 'PCS-RUNTIME-LOG-META-V1'
        status = 'STARTING'
        run_id = $runId
        gate_id = $GateId
        tool_id = $ToolId
        package_sha256 = $PackageSha256
        authorization_id = $AuthorizationId
        expected_run_root = $ExpectedRunRoot
        log_root = $resolved
        run_directory = $runDir
        started_utc = [DateTime]::UtcNow.ToString('o')
        host = [ordered]@{
            computer_name = $env:COMPUTERNAME
            os_version = [Environment]::OSVersion.VersionString
            powershell_version = $PSVersionTable.PSVersion.ToString()
            powershell_edition = [string]$PSVersionTable.PSEdition
        }
        privacy = [ordered]@{
            secrets_logged = $false
            broad_environment_dump = $false
        }
    }
    Write-PcsJsonAtomic -Path (Join-Path $runDir 'RUN_META.json') -Value $meta
    return [pscustomobject]@{
        RunId = $runId
        RunDir = $runDir
        LogRoot = $resolved
        GateId = $GateId
        ToolId = $ToolId
        StartedUtc = $meta.started_utc
    }
}

function Copy-PcsReturnArtifact {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory=$true)]$Context,
        [Parameter(Mandatory=$true)][string]$SourcePath
    )
    if (-not (Test-Path -LiteralPath $SourcePath -PathType Leaf)) {
        throw "PCS_LOG_RETURN_ARTIFACT_MISSING:$SourcePath"
    }
    $dest = Join-Path (Join-Path $Context.RunDir 'RETURN') ([IO.Path]::GetFileName($SourcePath))
    Copy-Item -LiteralPath $SourcePath -Destination $dest -Force
    return $dest
}

function Write-PcsResult {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory=$true)]$Context,
        [Parameter(Mandatory=$true)][ValidateSet('PASS','FAIL_CLOSED','BLOCKED','ABORTED')][string]$Status,
        [Parameter(Mandatory=$true)][int]$ExitCode,
        [string]$Phase = '',
        [string]$Detail = '',
        [bool]$GovernedActionInvoked = $true,
        [bool]$AutomaticRetryAuthorized = $false
    )
    $result = [ordered]@{
        schema = 'PCS-RUNTIME-LOG-RESULT-V1'
        run_id = $Context.RunId
        gate_id = $Context.GateId
        tool_id = $Context.ToolId
        status = $Status
        exit_code = $ExitCode
        phase = $Phase
        detail = $Detail
        governed_action_invoked = $GovernedActionInvoked
        automatic_retry_authorized = $AutomaticRetryAuthorized
        completed_utc = [DateTime]::UtcNow.ToString('o')
    }
    Write-PcsJsonAtomic -Path (Join-Path $Context.RunDir 'RESULT.json') -Value $result
    return $result
}

function Write-PcsRunManifest {
    [CmdletBinding()]
    param([Parameter(Mandatory=$true)]$Context)
    $runDir = $Context.RunDir
    $entries = @()
    Get-ChildItem -LiteralPath $runDir -File -Recurse | Sort-Object FullName | ForEach-Object {
        $rel = $_.FullName.Substring($runDir.Length)
        if ($rel.StartsWith([IO.Path]::DirectorySeparatorChar)) { $rel = $rel.Substring(1) }
        $rel = $rel.Replace('\','/')
        if ($rel -in @('RUN_MANIFEST.json','COMPLETE.marker')) { return }
        $entries += [ordered]@{
            path = $rel
            bytes = [int64]$_.Length
            sha256 = Get-PcsFileSha256 -Path $_.FullName
        }
    }
    $manifest = [ordered]@{
        schema = 'PCS-RUNTIME-LOG-MANIFEST-V1'
        run_id = $Context.RunId
        entry_count = $entries.Count
        entries = $entries
        recorded_utc = [DateTime]::UtcNow.ToString('o')
    }
    Write-PcsJsonAtomic -Path (Join-Path $runDir 'RUN_MANIFEST.json') -Value $manifest
    return $manifest
}

function Complete-PcsRunContext {
    [CmdletBinding()]
    param([Parameter(Mandatory=$true)]$Context)
    if (-not (Test-Path -LiteralPath (Join-Path $Context.RunDir 'RESULT.json') -PathType Leaf)) {
        throw 'PCS_LOG_RESULT_MISSING_BEFORE_COMPLETE'
    }
    $manifest = Write-PcsRunManifest -Context $Context
    $markerPath = Join-Path $Context.RunDir 'COMPLETE.marker'
    [System.IO.File]::WriteAllText($markerPath, $Context.RunId + "`r`n", [System.Text.UTF8Encoding]::new($false))
    return $manifest
}

function Test-PcsRunManifest {
    [CmdletBinding()]
    param([Parameter(Mandatory=$true)][string]$RunDirectory)
    $manifestPath = Join-Path $RunDirectory 'RUN_MANIFEST.json'
    $resultPath = Join-Path $RunDirectory 'RESULT.json'
    $completePath = Join-Path $RunDirectory 'COMPLETE.marker'
    if (-not (Test-Path -LiteralPath $manifestPath -PathType Leaf)) { return [pscustomobject]@{Pass=$false;Reason='MANIFEST_MISSING'} }
    if (-not (Test-Path -LiteralPath $resultPath -PathType Leaf)) { return [pscustomobject]@{Pass=$false;Reason='RESULT_MISSING'} }
    if (-not (Test-Path -LiteralPath $completePath -PathType Leaf)) { return [pscustomobject]@{Pass=$false;Reason='COMPLETE_MISSING'} }
    try { $manifest = Get-Content -LiteralPath $manifestPath -Raw | ConvertFrom-Json }
    catch { return [pscustomobject]@{Pass=$false;Reason='MANIFEST_JSON_INVALID'} }
    foreach ($entry in @($manifest.entries)) {
        $rel = [string]$entry.path
        $native = $rel.Replace('/', [IO.Path]::DirectorySeparatorChar)
        $path = Join-Path $RunDirectory $native
        if (-not (Test-Path -LiteralPath $path -PathType Leaf)) { return [pscustomobject]@{Pass=$false;Reason='PAYLOAD_MISSING';Path=$rel} }
        $fi = Get-Item -LiteralPath $path
        if ([int64]$fi.Length -ne [int64]$entry.bytes) { return [pscustomobject]@{Pass=$false;Reason='BYTE_MISMATCH';Path=$rel} }
        $sha = Get-PcsFileSha256 -Path $path
        if ($sha -ne ([string]$entry.sha256).ToLowerInvariant()) { return [pscustomobject]@{Pass=$false;Reason='SHA256_MISMATCH';Path=$rel} }
    }
    return [pscustomobject]@{Pass=$true;Reason='PASS';EntryCount=@($manifest.entries).Count}
}

Export-ModuleMember -Function Resolve-PcsLogRoot,Assert-PcsWritableLogRoot,New-PcsRunContext,Copy-PcsReturnArtifact,Write-PcsResult,Write-PcsRunManifest,Complete-PcsRunContext,Test-PcsRunManifest,Get-PcsFileSha256
