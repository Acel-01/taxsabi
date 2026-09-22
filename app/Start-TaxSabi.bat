@echo off
setlocal
cd /d "%~dp0"

if not exist "bin\llama-server.exe" (
  echo [!] Missing bin\llama-server.exe
  echo     Copy llama-server.exe from your llama.cpp build into the bin\ folder.
  pause
  exit /b 1
)

if not exist "model\TaxSabi-1.5B-Q4_K_M.gguf" (
  echo [!] Missing model\model file: model\TaxSabi-1.5B-Q4_K_M.gguf
  pause
  exit /b 1
)

echo Starting the TaxSabi engine...
start "TaxSabi Engine" /min bin\llama-server.exe ^
  -m model\TaxSabi-1.5B-Q4_K_M.gguf ^
  -c 2048 -t 4 --port 8080 --no-webui

echo Waiting for the engine to load...
timeout /t 4 /nobreak >nul

start "" "%~dp0TaxSabi.html"
echo.
echo TaxSabi is running. The engine keeps working in the background -
run Stop-TaxSabi.bat to shut it down.
pause
