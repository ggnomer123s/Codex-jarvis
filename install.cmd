@echo off
rem TIGO-CODEX MANAGED - double-click setup from a downloaded checkout
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0install.ps1" %*
set "TIGO_SETUP_EXIT=%ERRORLEVEL%"
if not "%TIGO_SETUP_EXIT%"=="0" pause
exit /b %TIGO_SETUP_EXIT%
