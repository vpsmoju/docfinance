@echo off
powershell -ExecutionPolicy Bypass -File "%~dp0\post-merge.ps1"
exit /b 0
