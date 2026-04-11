@echo off
setlocal enabledelayedexpansion

set "ROOT_DIR=%~dp0"
set "BACKEND_DIR=%ROOT_DIR%backend"
set "FRONTEND_DIR=%ROOT_DIR%frontend"

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

echo [INFO] Starting backend at http://127.0.0.1:8000 ...
start "Volunteer Backend" cmd /k "cd /d ""%BACKEND_DIR%"" && %PY_CMD% manage.py runserver 127.0.0.1:8000"

echo [INFO] Starting frontend at http://127.0.0.1:5173 ...
start "Volunteer Frontend" cmd /k "cd /d ""%FRONTEND_DIR%"" && npm run dev -- --host 127.0.0.1 --port 5173"

echo [DONE] Both services were launched in new windows.
echo [TIP] If browser did not open automatically, visit:
echo        http://127.0.0.1:5173

pause
