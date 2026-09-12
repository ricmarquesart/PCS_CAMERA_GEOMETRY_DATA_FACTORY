$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

$SourceRoot = 'C:\PCS_LABS\CAMERA_GEOMETRY_DATA_FACTORY\09_RUNS\DF_G101_SCALE1K_V1_R1'
$OutputRoot = 'C:\PCS_OUTPUTS\DF_G101_POST_R2_PHASE2_LOCAL_FIXTURES_V4'
$PassZip = Join-Path $OutputRoot 'DF_G101_POST_R2_PHASE2_LOCAL_COMPLETED_FIXTURES_RETURN_V4.zip'
$FailZip = Join-Path $OutputRoot 'DF_G101_POST_R2_PHASE2_LOCAL_COMPLETED_FIXTURES_FAILURE_RETURN_V4.zip'
$Stage = Join-Path $OutputRoot 'STAGING'
$SpecDriveId = '10CYQRkVLO5b8d4YRvlYW7k4uEIIB0VVB'
$ParentSpecDriveId = '1D7Zy-p9xLgE0-iNPWzmJv2m5D3BrVjwh'
$MethodBindingDriveId = '1go6KhawwDsAm4n25pATRsxw0ZwsoHgzZ'
$CloudCheckpointDriveId = '1CFWMXA1jGiBN45DcV9KVdfPBRawk9gTx'
$V1FailureAdjudicationDriveId = '1epzbZEg_WxHhRChrL-mqvz8L5VRRl8oL'
$V2FailureAdjudicationDriveId = '1dA8LO-Tm-4RCsSY1IpRFZdKmIxFf0GrS'
$V3OrderedDictionaryAddendumDriveId = '1OqSz0D-WvvKfi0ZiUb23a7bVKgS6wHXN'
$V3FailureAdjudicationDriveId = '1_K60VuSItxbci9JSZbWbEKWAK15Gu3fx'
$V4AuthorityBindingAddendumDriveId = '1SA0O0c9Hhj7EQiHkzykc2BoNotWzN5Ez'
$PathCompatibilityAddendumDriveId = '1YGdwiHt24AbqVriA5VDfK6hlLLmV1_3N'
$Phase = 'INIT'

function Write-JsonFile([string]$Path, $Object) {
    $json = $Object | ConvertTo-Json -Depth 100
    [System.IO.File]::WriteAllText($Path, $json + "`r`n", [System.Text.UTF8Encoding]::new($false))
}
function Hash-Info([string]$Path, [string]$Relative) {
    $fi = Get-Item -LiteralPath $Path -ErrorAction Stop
    $h = (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash.ToLowerInvariant()
    [ordered]@{
        relative_path = $Relative.Replace('\','/')
        bytes = [int64]$fi.Length
        sha256 = $h
        last_write_utc = $fi.LastWriteTimeUtc.ToString('o')
    }
}
function Zip-Directory([string]$Source, [string]$ZipPath) {
    Add-Type -AssemblyName System.IO.Compression.FileSystem
    if (Test-Path -LiteralPath $ZipPath) { Remove-Item -LiteralPath $ZipPath -Force }
    [System.IO.Compression.ZipFile]::CreateFromDirectory($Source, $ZipPath, [System.IO.Compression.CompressionLevel]::Optimal, $false)
}
function Fail-Closed([string]$Code, [string]$Detail, $ErrorRecord = $null) {
    try {
        New-Item -ItemType Directory -Force -Path $OutputRoot | Out-Null
        $fs = Join-Path $OutputRoot 'FAILURE_STAGING'
        if (Test-Path -LiteralPath $fs) { Remove-Item -LiteralPath $fs -Recurse -Force }
        New-Item -ItemType Directory -Force -Path $fs | Out-Null
        $exceptionType = $null
        $fullyQualifiedErrorId = $null
        $scriptStackTrace = $null
        $invocationPosition = $null
        if ($null -ne $ErrorRecord) {
            if ($null -ne $ErrorRecord.Exception) { $exceptionType = $ErrorRecord.Exception.GetType().FullName }
            $fullyQualifiedErrorId = [string]$ErrorRecord.FullyQualifiedErrorId
            $scriptStackTrace = [string]$ErrorRecord.ScriptStackTrace
            if ($null -ne $ErrorRecord.InvocationInfo) { $invocationPosition = [string]$ErrorRecord.InvocationInfo.PositionMessage }
        }
        $r = [ordered]@{
            schema='DF-G101-POST-R2-PHASE2-LOCAL-COLLECTOR-RESULT-V4'; status='FAIL_CLOSED'; code=$Code; detail=$Detail; phase=$Phase;
            exception_type=$exceptionType; fully_qualified_error_id=$fullyQualifiedErrorId; script_stack_trace=$scriptStackTrace; invocation_position=$invocationPosition;
            source_run_root=$SourceRoot; spec_drive_id=$SpecDriveId; parent_spec_drive_id=$ParentSpecDriveId; v1_failure_adjudication_drive_id=$V1FailureAdjudicationDriveId; v2_failure_adjudication_drive_id=$V2FailureAdjudicationDriveId; v3_failure_adjudication_drive_id=$V3FailureAdjudicationDriveId; path_compatibility_addendum_drive_id=$PathCompatibilityAddendumDriveId; v3_ordered_dictionary_addendum_drive_id=$V3OrderedDictionaryAddendumDriveId; v4_authority_binding_addendum_drive_id=$V4AuthorityBindingAddendumDriveId;
            blender_invoked=$false; renderer_invoked=$false; training_started=$false; test77_accessed=$false; maya_mutated=$false; product_mutated=$false;
            automatic_retry_authorized=$false; recorded_utc=[DateTime]::UtcNow.ToString('o')
        }
        Write-JsonFile (Join-Path $fs 'COLLECTOR_RESULT.json') $r
        Zip-Directory $fs $FailZip
    } catch { }
    Write-Host "FAIL_CLOSED: $Code"
    Write-Host $Detail
    Write-Host "Failure return: $FailZip"
    exit 2
}

try {
    $Phase = 'SOURCE_VALIDATE'
    if (-not (Test-Path -LiteralPath $SourceRoot -PathType Container)) { Fail-Closed 'SOURCE_RUN_ROOT_MISSING' $SourceRoot }
    $progressPath = Join-Path $SourceRoot 'PROGRESS.json'
    if (-not (Test-Path -LiteralPath $progressPath -PathType Leaf)) { Fail-Closed 'PROGRESS_MISSING' $progressPath }
    $progress = Get-Content -LiteralPath $progressPath -Raw | ConvertFrom-Json
    if ([int]$progress.completed -ne 34) { Fail-Closed 'PROGRESS_COMPLETED_NOT_34' ("actual=" + [string]$progress.completed) }

    $Phase = 'LEDGER_BIND'
    $requiredOrdinals = [System.Collections.Generic.List[int]]::new()
    0..33 | ForEach-Object { $requiredOrdinals.Add($_) }
    $sampleBindings = [System.Collections.Generic.List[object]]::new()
    $ledgerPaths = @{}

    foreach ($chunkIndex in 0..3) {
        $chunkName = ('chunk_{0:D3}' -f $chunkIndex)
        $chunkRoot = Join-Path (Join-Path $SourceRoot 'CHUNKS') $chunkName
        $ledgerPath = Join-Path $chunkRoot 'ledger.json'
        if (-not (Test-Path -LiteralPath $ledgerPath -PathType Leaf)) { Fail-Closed 'LEDGER_MISSING' $ledgerPath }
        $ledgerPaths[$chunkName] = $ledgerPath
        $ledger = Get-Content -LiteralPath $ledgerPath -Raw | ConvertFrom-Json
        foreach ($prop in $ledger.states.PSObject.Properties) {
            $sid = [string]$prop.Name
            if ($sid -notmatch '^g101v1_(\d{4})_') { continue }
            $ordinal = [int]$Matches[1]
            if ($ordinal -lt 0 -or $ordinal -gt 33) { continue }
            $expectedChunk = [math]::Floor($ordinal / 10)
            if ($expectedChunk -ne $chunkIndex) { Fail-Closed 'SAMPLE_CHUNK_BINDING_MISMATCH' "$sid expected_chunk=$expectedChunk actual_chunk=$chunkIndex" }
            $state = [string]$prop.Value.state
            if ($state -ne 'COMPLETE') { Fail-Closed 'REQUIRED_SAMPLE_NOT_COMPLETE' "$sid state=$state" }
            $reqPath = Join-Path (Join-Path $chunkRoot 'requests') ($sid + '.json')
            $sampleDir = Join-Path (Join-Path $chunkRoot 'samples') $sid
            if (-not (Test-Path -LiteralPath $reqPath -PathType Leaf)) { Fail-Closed 'REQUEST_MISSING' $reqPath }
            if (-not (Test-Path -LiteralPath $sampleDir -PathType Container)) { Fail-Closed 'SAMPLE_DIR_MISSING' $sampleDir }
            $sampleBindings.Add([ordered]@{ ordinal=$ordinal; sample_id=$sid; chunk=$chunkName; request_path=$reqPath; sample_dir=$sampleDir })
        }
    }

    $Phase = 'BINDING_VALIDATE'
    if ($sampleBindings.Count -ne 34) { Fail-Closed 'COMPLETED_SAMPLE_COUNT_NOT_34' ("actual=" + $sampleBindings.Count) }
    $ords = [int[]]($sampleBindings | ForEach-Object { [int]$_.ordinal } | Sort-Object)
    for ($i=0; $i -lt 34; $i++) { if ($ords[$i] -ne $i) { Fail-Closed 'ORDINAL_SET_MISMATCH' ("index=$i value=" + $ords[$i]) } }
    $seenSampleIds = @{}
    foreach ($b in ($sampleBindings | Sort-Object -Property { [int]$_['ordinal'] })) {
        $sidCheck = [string]$b['sample_id']
        if ([string]::IsNullOrWhiteSpace($sidCheck)) { Fail-Closed 'EMPTY_SAMPLE_ID' '' }
        if ($seenSampleIds.ContainsKey($sidCheck)) { Fail-Closed 'DUPLICATE_SAMPLE_ID' $sidCheck }
        $seenSampleIds[$sidCheck] = $true
    }
    if ($seenSampleIds.Count -ne 34) { Fail-Closed 'UNIQUE_SAMPLE_ID_COUNT_NOT_34' ("actual=" + $seenSampleIds.Count) }

    $Phase = 'STAGE_PREPARE'
    New-Item -ItemType Directory -Force -Path $OutputRoot | Out-Null
    if (Test-Path -LiteralPath $Stage) { Remove-Item -LiteralPath $Stage -Recurse -Force }
    New-Item -ItemType Directory -Force -Path $Stage | Out-Null
    New-Item -ItemType Directory -Force -Path (Join-Path $Stage 'FIXTURES') | Out-Null
    New-Item -ItemType Directory -Force -Path (Join-Path $Stage 'LEDGERS') | Out-Null

    $sources = [System.Collections.Generic.List[object]]::new()
    $copyJobs = [System.Collections.Generic.List[object]]::new()
    $copyJobs.Add([ordered]@{ source=$progressPath; dest=(Join-Path $Stage 'PROGRESS.json'); rel='PROGRESS.json' })
    foreach ($chunkName in @('chunk_000','chunk_001','chunk_002','chunk_003')) {
        $src = [string]$ledgerPaths[$chunkName]
        $destRel = 'LEDGERS/' + $chunkName + '_ledger.json'
        $copyJobs.Add([ordered]@{ source=$src; dest=(Join-Path $Stage ($destRel.Replace('/','\'))); rel=('CHUNKS/' + $chunkName + '/ledger.json') })
    }
    foreach ($b in ($sampleBindings | Sort-Object -Property { [int]$_['ordinal'] })) {
        $sid = [string]$b.sample_id
        $fixtureRoot = Join-Path (Join-Path $Stage 'FIXTURES') $sid
        $reqDest = Join-Path $fixtureRoot 'request.json'
        $reqRel = 'CHUNKS/' + $b.chunk + '/requests/' + $sid + '.json'
        $copyJobs.Add([ordered]@{ source=[string]$b.request_path; dest=$reqDest; rel=$reqRel })
        Get-ChildItem -LiteralPath ([string]$b.sample_dir) -File -Recurse | Sort-Object FullName | ForEach-Object {
            $sampleRoot = [string]$b.sample_dir
            $sub = $_.FullName.Substring($sampleRoot.Length)
            if ($sub.StartsWith('\')) { $sub = $sub.Substring(1) }
            $dest = Join-Path (Join-Path $fixtureRoot 'sample') $sub
            $rel = 'CHUNKS/' + $b.chunk + '/samples/' + $sid + '/' + ($sub.Replace('\','/'))
            $copyJobs.Add([ordered]@{ source=$_.FullName; dest=$dest; rel=$rel })
        }
    }

    $Phase = 'SOURCE_HASH'
    $seen = @{}
    foreach ($j in $copyJobs) {
        if ($seen.ContainsKey([string]$j.rel)) { Fail-Closed 'DUPLICATE_SOURCE_RELATIVE_PATH' ([string]$j.rel) }
        $seen[[string]$j.rel] = $true
        $sources.Add((Hash-Info ([string]$j.source) ([string]$j.rel)))
    }
    $Phase = 'SOURCE_MANIFEST_WRITE'
    Write-JsonFile (Join-Path $Stage 'SOURCE_BEFORE_MANIFEST.json') ([ordered]@{schema='DF-G101-PHASE2-SOURCE-MANIFEST-V4'; entries=$sources.ToArray()})

    $Phase = 'COPY'
    foreach ($j in $copyJobs) {
        $parent = Split-Path -Parent ([string]$j.dest)
        New-Item -ItemType Directory -Force -Path $parent | Out-Null
        Copy-Item -LiteralPath ([string]$j.source) -Destination ([string]$j.dest) -Force
    }

    $Phase = 'POST_COPY_VERIFY'
    $staged = [System.Collections.Generic.List[object]]::new()
    $after = [System.Collections.Generic.List[object]]::new()
    $copyMismatch = [System.Collections.Generic.List[string]]::new()
    $sourceMutation = [System.Collections.Generic.List[string]]::new()
    for ($i=0; $i -lt $copyJobs.Count; $i++) {
        $j = $copyJobs[$i]
        $before = $sources[$i]
        $si = Hash-Info ([string]$j.dest) ([string]$j.rel)
        $ai = Hash-Info ([string]$j.source) ([string]$j.rel)
        $staged.Add($si); $after.Add($ai)
        if ($before.bytes -ne $si.bytes -or $before.sha256 -ne $si.sha256) { $copyMismatch.Add([string]$j.rel) }
        if ($before.bytes -ne $ai.bytes -or $before.sha256 -ne $ai.sha256 -or $before.last_write_utc -ne $ai.last_write_utc) { $sourceMutation.Add([string]$j.rel) }
    }
    Write-JsonFile (Join-Path $Stage 'STAGED_MANIFEST.json') ([ordered]@{schema='DF-G101-PHASE2-STAGED-MANIFEST-V4'; entries=$staged.ToArray()})
    Write-JsonFile (Join-Path $Stage 'SOURCE_AFTER_MANIFEST.json') ([ordered]@{schema='DF-G101-PHASE2-SOURCE-MANIFEST-V4'; entries=$after.ToArray()})
    if ($copyMismatch.Count -ne 0) { Fail-Closed 'STAGED_COPY_HASH_MISMATCH' (($copyMismatch | Select-Object -First 20) -join ',') }
    if ($sourceMutation.Count -ne 0) { Fail-Closed 'SOURCE_MUTATION_DETECTED' (($sourceMutation | Select-Object -First 20) -join ',') }

    $Phase = 'RESULT_WRITE'
    [int64]$totalBytes = 0
    foreach ($entry in $sources) { $totalBytes += [int64]$entry['bytes'] }
    [string[]]$completedIds = $sampleBindings | Sort-Object -Property { [int]$_['ordinal'] } | ForEach-Object { [string]$_['sample_id'] }
    $result = [ordered]@{
        schema='DF-G101-POST-R2-PHASE2-LOCAL-COLLECTOR-RESULT-V4'; status='PASS';
        source_run_root=$SourceRoot; destination_root=$OutputRoot;
        spec_drive_id=$SpecDriveId; parent_spec_drive_id=$ParentSpecDriveId; method_binding_drive_id=$MethodBindingDriveId; cloud_checkpoint_drive_id=$CloudCheckpointDriveId; v1_failure_adjudication_drive_id=$V1FailureAdjudicationDriveId; v2_failure_adjudication_drive_id=$V2FailureAdjudicationDriveId; v3_failure_adjudication_drive_id=$V3FailureAdjudicationDriveId; path_compatibility_addendum_drive_id=$PathCompatibilityAddendumDriveId; v3_ordered_dictionary_addendum_drive_id=$V3OrderedDictionaryAddendumDriveId; v4_authority_binding_addendum_drive_id=$V4AuthorityBindingAddendumDriveId;
        completed_sample_count=34; completed_sample_ids=$completedIds;
        source_file_count=$sources.Count; source_total_bytes=$totalBytes;
        before_staged_equal_count=$sources.Count; before_after_equal_count=$sources.Count; copy_mismatch_count=0; source_mutation_count=0;
        run_root_mutated=$false; blender_invoked=$false; renderer_invoked=$false; training_started=$false; test77_accessed=$false; maya_mutated=$false; product_mutated=$false;
        automatic_retry_authorized=$false; recorded_utc=[DateTime]::UtcNow.ToString('o')
    }
    Write-JsonFile (Join-Path $Stage 'COLLECTOR_RESULT.json') $result

    $Phase = 'RETURN_MANIFEST_WRITE'
    $manifestEntries = [System.Collections.Generic.List[object]]::new()
    Get-ChildItem -LiteralPath $Stage -File -Recurse | Where-Object { $_.Name -ne 'RETURN_MANIFEST.json' } | Sort-Object FullName | ForEach-Object {
        $rel = $_.FullName.Substring($Stage.Length)
        if ($rel.StartsWith('\')) { $rel = $rel.Substring(1) }
        $rel = $rel.Replace('\','/')
        $manifestEntries.Add([ordered]@{path=$rel;bytes=[int64]$_.Length;sha256=(Get-FileHash -LiteralPath $_.FullName -Algorithm SHA256).Hash.ToLowerInvariant()})
    }
    Write-JsonFile (Join-Path $Stage 'RETURN_MANIFEST.json') ([ordered]@{schema='DF-G101-POST-R2-PHASE2-LOCAL-RETURN-MANIFEST-V4'; entries=$manifestEntries.ToArray()})
    $Phase = 'ZIP_WRITE'
    Zip-Directory $Stage $PassZip

    Write-Host 'PASS - read-only fixture collection complete.'
    Write-Host ('Samples: ' + $sampleBindings.Count)
    Write-Host ('Source files: ' + $sources.Count)
    Write-Host ('Return ZIP: ' + $PassZip)
    exit 0
}
catch {
    $er = $_
    Fail-Closed 'UNHANDLED_COLLECTOR_EXCEPTION' ($er.Exception.GetType().FullName + ': ' + $er.Exception.Message) $er
}
