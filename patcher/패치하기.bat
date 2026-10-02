@echo off
rem Drag a Japanese Star Fox Adventures (GSAJ01 Rev 1) image onto this file, or put it in this folder and double-click.
cd /d "%~dp0"
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0patch.ps1" %*
set rc=%errorlevel%
pause
exit /b %rc%
