@echo off
SETLOCAL

echo Anonyfiles - Script CMD
echo -------------------------
echo Available commands:
echo   setup  : Create Python virtual environments
echo   api    : Launch FastAPI server
echo   cli    : Run CLI engine
echo   gui    : Launch GUI (Tauri)
echo   clean  : Remove all environments
echo.

set ACTION=%1

IF "%ACTION%"=="setup" (
    call setup_envs.bat
) ELSE IF "%ACTION%"=="api" (
    call env-api\Scripts\activate.bat
    python anonyfiles_api\api.py
) ELSE IF "%ACTION%"=="cli" (
    call env-cli\Scripts\activate.bat
    python anonyfiles-cli\main.py
) ELSE IF "%ACTION%"=="gui" (
    cd anonyfiles-gui
    npm run tauri dev
) ELSE IF "%ACTION%"=="clean" (
    rmdir /S /Q env-cli
    rmdir /S /Q env-api
    rmdir /S /Q env-gui
) ELSE (
    echo Invalid action. Use: setup, api, cli, gui or clean.
)

ENDLOCAL
