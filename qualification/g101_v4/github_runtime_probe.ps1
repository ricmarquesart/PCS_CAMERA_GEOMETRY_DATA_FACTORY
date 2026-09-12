param(
    [Parameter(Mandatory=$true)][string]$CollectorPath,
    [Parameter(Mandatory=$true)][string]$LauncherPath
)

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

function Assert-True([bool]$Condition, [string]$Message) {
    if (-not $Condition) { throw "ASSERTION_FAILED: $Message" }
}

Write-Host "PowerShell version: $($PSVersionTable.PSVersion)"
Write-Host "PSEdition: $($PSVersionTable.PSEdition)"
Write-Host "Collector: $CollectorPath"

Assert-True (Test-Path -LiteralPath $CollectorPath -PathType Leaf) 'collector file missing'
Assert-True (Test-Path -LiteralPath $LauncherPath -PathType Leaf) 'launcher file missing'

# 1) Parse the exact V4 collector source without executing it.
$tokens = $null
$parseErrors = $null
[void][System.Management.Automation.Language.Parser]::ParseFile($CollectorPath, [ref]$tokens, [ref]$parseErrors)
if ($parseErrors.Count -gt 0) {
    $parseErrors | ForEach-Object { Write-Host $_.Message }
    throw "collector has $($parseErrors.Count) PowerShell parse error(s)"
}
Write-Host 'PASS: PowerShell parser accepted collector source.'

$collector = Get-Content -LiteralPath $CollectorPath -Raw
$launcher = Get-Content -LiteralPath $LauncherPath -Raw

# 2) Static contract for the V4 compatibility correction.
Assert-True (-not $collector.Contains('New-Object System.Collections.Generic.List')) 'legacy New-Object generic List pattern remains'
foreach ($name in @('sources','staged','after','manifestEntries')) {
    Assert-True (-not $collector.Contains('@($' + $name + ')')) ("direct array-subexpression remains for " + $name)
    Assert-True ($collector.Contains('$' + $name + '.ToArray()')) ("missing .ToArray() materialization for " + $name)
}
Assert-True ($collector.Contains('[string]$b[''sample_id'']')) 'explicit sample_id dictionary-key access missing'
Assert-True ($collector.Contains('Sort-Object -Property { [int]$_[''ordinal''] }')) 'explicit ordinal-key sort missing'
Assert-True ($collector.Contains('[int64]$entry[''bytes'']')) 'explicit bytes-key accumulation missing'
foreach ($phase in @('SOURCE_VALIDATE','LEDGER_BIND','BINDING_VALIDATE','STAGE_PREPARE','SOURCE_HASH','SOURCE_MANIFEST_WRITE','COPY','POST_COPY_VERIFY','RESULT_WRITE','RETURN_MANIFEST_WRITE','ZIP_WRITE')) {
    $phaseNeedle = '$Phase = ''' + $phase + ''''
    Assert-True ($collector.Contains($phaseNeedle)) ("missing phase marker: " + $phase)
}
$expectedLauncherInvocation = 'powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0COLLECT_PHASE2_LOCAL_FIXTURES.ps1"'
Assert-True ($launcher.Contains($expectedLauncherInvocation)) 'launcher does not target the bundled collector exactly'
$invocationLikeLines = @(
    $launcher -split "`r?`n" |
        ForEach-Object { $_.Trim() } |
        Where-Object {
            $_ -and
            $_ -notmatch '^(?i)@?echo\b' -and
            $_ -match '(?i)(powershell(?:\.exe)?|pwsh(?:\.exe)?|python(?:\.exe)?|blender(?:\.exe)?|maya(?:\.exe)?|\.py\b|\.ps1\b|\.bat\b)'
        }
)
Assert-True ($invocationLikeLines.Count -eq 1) ('launcher has unexpected executable/script invocation line(s): ' + ($invocationLikeLines -join ' || '))
Assert-True ($invocationLikeLines[0] -eq $expectedLauncherInvocation) ('launcher invocation differs from frozen bundled collector call: ' + $invocationLikeLines[0])
Write-Host 'PASS: frozen V4 static compatibility contract is present.'

# 3) Exercise the exact object/materialization mechanisms that replaced the V3 binder path.
$orderedEntries = [System.Collections.Generic.List[object]]::new()
$orderedEntries.Add([ordered]@{ ordinal = 2; sample_id = 'g101v1_0002_probe'; bytes = [int64]22 })
$orderedEntries.Add([ordered]@{ ordinal = 0; sample_id = 'g101v1_0000_probe'; bytes = [int64]10 })
$orderedEntries.Add([ordered]@{ ordinal = 1; sample_id = 'g101v1_0001_probe'; bytes = [int64]11 })

$materialized = $orderedEntries.ToArray()
Assert-True ($materialized.Count -eq 3) '.ToArray() did not preserve List[object] item count'
$json = ([ordered]@{ schema='G101-V4-GITHUB-RUNTIME-PROBE'; entries=$materialized } | ConvertTo-Json -Depth 20)
$roundTrip = $json | ConvertFrom-Json
Assert-True ($roundTrip.entries.Count -eq 3) 'JSON round-trip did not preserve array cardinality'

$sorted = @($orderedEntries | Sort-Object -Property { [int]$_['ordinal'] })
$sortedOrdinals = ($sorted | ForEach-Object { [int]$_['ordinal'] }) -join ','
Assert-True ($sortedOrdinals -eq '0,1,2') 'explicit ordinal dictionary-key sort failed'

$seen = @{}
foreach ($b in $sorted) {
    $sid = [string]$b['sample_id']
    Assert-True (-not [string]::IsNullOrWhiteSpace($sid)) 'sample_id became empty'
    Assert-True (-not $seen.ContainsKey($sid)) 'duplicate sample_id in positive runtime probe'
    $seen[$sid] = $true
}
Assert-True ($seen.Count -eq 3) 'seen-id map count mismatch'

[int64]$totalBytes = 0
foreach ($entry in $orderedEntries) { $totalBytes += [int64]$entry['bytes'] }
Assert-True ($totalBytes -eq 43) 'explicit bytes-key accumulation failed'

$stringList = [System.Collections.Generic.List[string]]::new()
$stringList.Add('a'); $stringList.Add('b')
Assert-True (($stringList.ToArray() -join ',') -eq 'a,b') 'List[string].ToArray() failed'
Write-Host 'PASS: V4 generic-list, ordered-dictionary, sort, byte-sum, and JSON materialization paths executed successfully.'

# 4) Diagnostic-only reproduction attempt for the retired V3 pattern. This is not a gate:
# runner PowerShell versions may differ, so absence of reproduction does not invalidate V4.
$legacyReproduced = $false
$legacyDetail = $null
try {
    $legacy = New-Object 'System.Collections.Generic.List[object]'
    $legacy.Add([ordered]@{ x = 1 })
    $null = @($legacy)
} catch {
    $legacyReproduced = $true
    $legacyDetail = $_.Exception.GetType().FullName + ': ' + $_.Exception.Message
}
Write-Host ("INFO: retired V3 binder reproduction on this runtime = " + $legacyReproduced)
if ($legacyDetail) { Write-Host ("INFO: retired V3 binder detail = " + $legacyDetail) }

Write-Host 'G101 V4 WINDOWS RUNTIME PREFLIGHT: PASS'
