@echo off
setlocal
cd /d %~dp0
if exist dist\MailOutreachAgent\MailOutreachAgent.exe (
  start "" dist\MailOutreachAgent\MailOutreachAgent.exe
) else (
  echo EXE not found. Run build_windows.bat first.
  pause
)
endlocal
