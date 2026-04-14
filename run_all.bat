@echo off
setlocal enabledelayedexpansion

set "ROOT_DIR=%~dp0"
set "BACKEND_DIR=%ROOT_DIR%backend"
set "FRONTEND_DIR=%ROOT_DIR%frontend"
set "HOST=0.0.0.0"
set "BACKEND_PORT=8000"
set "FRONTEND_PORT=5173"

if not exist "%BACKEND_DIR%\manage.py" (
  echo [ERROR] backend\manage.py not found.
  pause
  exit /b 1
)

if not exist "%FRONTEND_DIR%\package.json" (
  echo [ERROR] frontend\package.json not found.
  pause
  exit /b 1
)

where npm >nul 2>nul
if errorlevel 1 (
  echo [ERROR] npm not found in PATH. Please install Node.js first.
  pause
  exit /b 1
)

set "PY_CMD=python"
where conda >nul 2>nul
if not errorlevel 1 (
  set "PY_CMD=conda run -n base_env python"
)
if "%PY_CMD%"=="python" (
  where python >nul 2>nul
  if errorlevel 1 (
    echo [ERROR] python not found in PATH.
    pause
    exit /b 1
  )
)

echo [INFO] Using Python command: %PY_CMD%

set "GET_IP_SCRIPT=%ROOT_DIR%scripts\get_local_ip.ps1"
if exist "%GET_IP_SCRIPT%" (
  for /f %%i in ('powershell -NoProfile -ExecutionPolicy Bypass -File "%GET_IP_SCRIPT%"') do set "LOCAL_IP=%%i"
)
if not defined LOCAL_IP set "LOCAL_IP=127.0.0.1"

echo [INFO] Running backend migrations...
pushd "%BACKEND_DIR%"
call %PY_CMD% manage.py migrate
if errorlevel 1 (
  echo [ERROR] Migration failed. Please check Python environment/base_env.
  popd
  pause
  exit /b 1
)
popd

if not exist "%FRONTEND_DIR%\node_modules" (
  echo [INFO] Installing frontend dependencies...
  pushd "%FRONTEND_DIR%"
  call npm install
  if errorlevel 1 (
    echo [ERROR] npm install failed.
    popd
    pause
    exit /b 1
  )
  popd
)

echo [INFO] Starting backend at http://%HOST%:%BACKEND_PORT% ...
start "Volunteer Backend" cmd /k "cd /d ""%BACKEND_DIR%"" && %PY_CMD% manage.py runserver %HOST%:%BACKEND_PORT%"

echo [INFO] Starting frontend at http://%HOST%:%FRONTEND_PORT% ...
start "Volunteer Frontend" cmd /k "cd /d ""%FRONTEND_DIR%"" && npm run dev -- --host %HOST% --port %FRONTEND_PORT%"

echo [DONE] Both services were launched in new windows.
echo [TIP] If browser did not open automatically, visit:
echo        Local:    http://127.0.0.1:%FRONTEND_PORT%
echo        LAN:      http://%LOCAL_IP%:%FRONTEND_PORT%
echo [TIP] Open the LAN address on your phone (same Wi-Fi).

pause
