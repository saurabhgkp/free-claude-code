@echo off
setlocal

echo ============================================================
echo  free-claude-code  --  PyInstaller build
echo ============================================================
echo.

:: Install / upgrade PyInstaller inside the project venv
echo [1/3] Installing PyInstaller...
python -m uv pip install pyinstaller
if errorlevel 1 (
    echo ERROR: could not install PyInstaller
    pause & exit /b 1
)

echo.
echo [2/3] Building executable (this takes 10-20 minutes)...
echo.

python -m PyInstaller ^
  --onefile ^
  --name free-claude-code ^
  --console ^
  --collect-all uvicorn ^
  --collect-all fastapi ^
  --collect-all pydantic ^
  --collect-all pydantic_settings ^
  --collect-all tiktoken ^
  --collect-all openai ^
  --collect-all httpx ^
  --collect-all loguru ^
  --collect-all telegram ^
  --collect-all markdown_it ^
  --hidden-import uvicorn.loops.asyncio ^
  --hidden-import uvicorn.protocols.http.h11_impl ^
  --hidden-import uvicorn.protocols.websockets.auto ^
  --hidden-import uvicorn.lifespan.on ^
  --hidden-import uvicorn.lifespan.off ^
  --hidden-import uvicorn.logging ^
  --hidden-import fastapi.responses ^
  --hidden-import fastapi.middleware ^
  --hidden-import pydantic.v1 ^
  --hidden-import email_validator ^
  --hidden-import anyio._backends._asyncio ^
  --hidden-import anyio._backends._trio ^
  app_entry.py

if errorlevel 1 (
    echo.
    echo ERROR: build failed. See output above.
    pause & exit /b 1
)

echo.
echo [3/3] Done!
echo.
echo Output: dist\free-claude-code.exe
echo.
echo Before running, place a .env file next to the .exe with:
echo   NVIDIA_NIM_API_KEY=nvapi-...
echo   TELEGRAM_BOT_TOKEN=your-token
echo   ALLOWED_TELEGRAM_USER_ID=your-id
echo.

pause
