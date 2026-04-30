@echo off
setlocal
cd /d %~dp0
python -m venv .venv
call .venv\Scripts\activate
python -m pip install --upgrade pip
pip install -r requirements.txt
pyinstaller --name MailOutreachAgent --noconfirm --windowed --onefile app\main.py
echo Build completed. See dist\
endlocal
