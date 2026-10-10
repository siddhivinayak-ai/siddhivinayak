@echo off
REM Starts Siddhivinayak: brain (5060), voice (5050) and the 3D site (5173).
cd /d "%~dp0"

if not exist venv\Scripts\python.exe (
  echo Creating Python environment...
  python -m venv venv
  venv\Scripts\python -m pip install -r server\requirements.txt
)
if not exist node_modules (
  echo Installing web dependencies...
  call npm install
)
if not exist server\.env (
  echo.
  echo  No server\.env found - copy server\.env.example to server\.env and add an API key.
  echo  Starting anyway in offline retrieval mode.
  echo.
)

start "Siddhivinayak brain" cmd /k "cd server && ..\venv\Scripts\python brain_server.py"
start "Siddhivinayak voice" cmd /k "cd server && ..\venv\Scripts\python tts_server.py"
start "Siddhivinayak site" cmd /k "npx vite --port 5173"

timeout /t 4 >nul
start http://localhost:5173
