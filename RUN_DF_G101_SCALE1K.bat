@echo off
setlocal
cd /d "%~dp0"
echo ================================================================
echo PCS CAMERA GEOMETRY DATA FACTORY - DF-G101 SCALE1K V1 - R2 RECOVERY
echo ================================================================
echo.
echo This package is authorized only for the exact existing R1 fail-closed run-root.
echo It MUST preserve samples 0000-0009 and MUST NOT rerender them.
echo Expected recovery: sample0005 existing-bytes RGB x2, accept 0006-0009, continue at 0010.
echo.
echo Expected success transport:
echo   1 RETURN INDEX ZIP
echo   10 RETURN SHARD ZIPs, each covering 100 samples
echo.
echo IMPORTANT:
echo   - Do not run R1 again.
echo   - Do not delete, reset, rename, recreate, or manually edit the G101 run-root.
echo   - Run this R2 package exactly once.
echo   - On any failure, return the FAILURE_RETURN and Guardian result; do not rerun.
echo.
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0RUN_DF_G101_SCALE1K_GUARDIAN.ps1"
set RC=%ERRORLEVEL%
echo.
if "%RC%"=="0" (
  echo ================================================================
  echo DF-G101 R2 SCALE1K RESULT: MEASUREMENT COMPLETE - REVIEW REQUIRED
  echo ================================================================
  echo Return the INDEX ZIP and all ten RETURN_SHARD ZIPs.
) else (
  echo ================================================================
  echo DF-G101 R2 SCALE1K RESULT: FAIL CLOSED ^(RC=%RC%^)
  echo ================================================================
  echo Preserve all output and do not rerun before adjudication.
)
echo.
pause
exit /b %RC%
