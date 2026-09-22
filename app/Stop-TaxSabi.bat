@echo off
taskkill /f /im llama-server.exe >nul 2>&1
echo TaxSabi engine stopped.
timeout /t 2 /nobreak >nul
