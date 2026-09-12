@echo off
setlocal
cd /d "%~dp0"
echo ================================================================
echo DF-G101 POST-R2 PHASE2 - READ-ONLY LOCAL FIXTURE COLLECTOR V4
echo ================================================================
echo.
echo SOURCE (READ ONLY): C:\PCS_LABS\CAMERA_GEOMETRY_DATA_FACTORY\09_RUNS\DF_G101_SCALE1K_V1_R1
echo OUTPUT:             C:\PCS_OUTPUTS\DF_G101_POST_R2_PHASE2_LOCAL_FIXTURES_V4
echo.
echo This does NOT run Blender, Maya, training, or the G101 generator.
echo Do not close this window while hashes/copies are being verified.
echo.
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0COLLECT_PHASE2_LOCAL_FIXTURES.ps1"
set RC=%ERRORLEVEL%
echo.
if "%RC%"=="0" (
  echo PASS. Upload this file back to ChatGPT:
  echo C:\PCS_OUTPUTS\DF_G101_POST_R2_PHASE2_LOCAL_FIXTURES_V4\DF_G101_POST_R2_PHASE2_LOCAL_COMPLETED_FIXTURES_RETURN_V4.zip
) else (
  echo FAIL_CLOSED. Do not rerun automatically. Upload the FAILURE_RETURN ZIP instead.
)
echo.
pause
exit /b %RC%
