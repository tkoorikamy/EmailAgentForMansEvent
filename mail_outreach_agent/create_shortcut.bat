@echo off
setlocal
cd /d %~dp0
set "TARGET=%CD%\dist\MailOutreachAgent\MailOutreachAgent.exe"
set "SHORTCUT=%USERPROFILE%\Desktop\MailOutreachAgent.lnk"
if not exist "%TARGET%" (
  echo EXE not found: %TARGET%
  echo Build app first using build_windows.bat
  pause
  exit /b 1
)
powershell -NoProfile -ExecutionPolicy Bypass -Command "$s=(New-Object -COM WScript.Shell).CreateShortcut('%SHORTCUT%');$s.TargetPath='%TARGET%';$s.WorkingDirectory='%CD%';$s.Save()"
echo Shortcut created: %SHORTCUT%
endlocal
