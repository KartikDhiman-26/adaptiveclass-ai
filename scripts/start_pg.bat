@echo off
set "PG_BIN=C:\Program Files\PostgreSQL\17\bin"
set "PGDATA=d:\Zinnovatio 4.0\backend\pgdata"

echo Starting PostgreSQL on port 5433...
"%PG_BIN%\pg_ctl.exe" -D "%PGDATA%" -l "%PGDATA%\server.log" -o "-p 5433" start
if %ERRORLEVEL% equ 0 (
    echo PostgreSQL is running on port 5433.
    "%PG_BIN%\createdb.exe" -h localhost -p 5433 -U postgres adaptive_db 2>nul
    echo Database adaptive_db ready.
) else (
    echo Failed to start PostgreSQL!
    exit /b %ERRORLEVEL%
)
