@echo off
set "PG_BIN=C:\Program Files\PostgreSQL\17\bin"
set "PGDATA=d:\Zinnovatio 4.0\backend\pgdata"

echo Setting up dedicated PostgreSQL cluster at %PGDATA%...
if exist "%PGDATA%" (
    echo %PGDATA% already exists. Skipping initdb.
) else (
    "%PG_BIN%\initdb.exe" -D "%PGDATA%" -U postgres -A trust --no-locale --encoding=UTF8
    if %ERRORLEVEL% neq 0 (
        echo initdb failed!
        exit /b %ERRORLEVEL%
    )
    echo PostgreSQL cluster initialized successfully.
)
