@echo off
REM Switch to the script's directory
cd /d "%~dp0"

REM Check if virtual environment exists
IF NOT EXIST ".venv" (
    echo [PDF-Parser] Creating virtual environment...
    python -m venv .venv
)

REM Install dependencies (quietly) to ensure they are up to date
echo [PDF-Parser] Checking dependencies...
.venv\Scripts\pip install -q -r requirements.txt
.venv\Scripts\pip install pymupdf4llm

REM Run the server using the virtual environment python
echo [PDF-Parser] Starting Server...
.venv\Scripts\python server.py
