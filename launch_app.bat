@echo off
cmd /k ".\.venv\Scripts\activate"
cmd /k "pip install -r requirements.txt"
cmd /k "python main.py"
pause