@echo off
cd /d "%~dp0"

echo ============================================
echo   AI Social Media Agent - Startup
echo ============================================
echo.

:: -------------------------------------------
:: 1. Check Docker
:: -------------------------------------------
docker info >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Docker is not running. Start Docker Desktop first.
    pause
    exit /b 1
)

:: -------------------------------------------
:: 2. Start Postgres + Redis
:: -------------------------------------------
echo [1/5] Starting Postgres and Redis...
docker compose up -d postgres redis
if errorlevel 1 (
    echo [ERROR] Docker compose failed.
    pause
    exit /b 1
)

echo Waiting for Postgres to be ready...
timeout /t 8 /nobreak >nul

:: -------------------------------------------
:: 3. Run migrations
:: -------------------------------------------
echo [2/5] Running database migrations...
set PYTHONPATH=%~dp0backend
"%~dp0.venv\Scripts\python.exe" -m alembic upgrade head
if errorlevel 1 (
    echo [WARNING] Migration failed - continuing anyway.
)

:: -------------------------------------------
:: 4. Kill old processes on port 8000
:: -------------------------------------------
echo [3/5] Checking for port conflicts...
netstat -aon 2>nul | findstr ":8000.*LISTENING" >"%TEMP%\port8000.txt" 2>nul
for /f "tokens=5" %%p in (%TEMP%\port8000.txt) do (
    echo Killing old process on port 8000 PID %%p
    taskkill /F /PID %%p >nul 2>&1
)
del "%TEMP%\port8000.txt" >nul 2>&1

:: -------------------------------------------
:: 5. Start services in separate windows
:: -------------------------------------------
echo [4/5] Starting backend, Celery, and frontend...

start "API Server" cmd /k "cd /d "%~dp0" && set PYTHONPATH=%~dp0backend&& "%~dp0.venv\Scripts\python.exe" -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload --app-dir backend"

timeout /t 3 /nobreak >nul

start "Celery Worker" cmd /k "cd /d "%~dp0" && set PYTHONPATH=%~dp0backend&& "%~dp0.venv\Scripts\celery.exe" -A app.core.celery_app.celery_app worker --loglevel=info --pool=solo"

start "Celery Beat" cmd /k "cd /d "%~dp0" && set PYTHONPATH=%~dp0backend&& "%~dp0.venv\Scripts\celery.exe" -A app.core.celery_app.celery_app beat --loglevel=info"

start "Frontend" cmd /k "cd /d "%~dp0frontend" && npm run dev"

:: -------------------------------------------
:: 6. Wait and verify
:: -------------------------------------------
echo [5/5] Waiting for services to start...
timeout /t 8 /nobreak >nul

echo.
echo ============================================
echo   All services launched!
echo ============================================
echo.
echo   Frontend  : http://localhost:3000
echo   Backend   : http://localhost:8000
echo   API Docs  : http://localhost:8000/docs
echo.
echo   4 windows opened - keep them running.
echo   Press any key to close this launcher.
echo ============================================
pause
