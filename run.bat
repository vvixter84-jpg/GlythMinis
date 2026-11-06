@echo off
rem GlythMinis launcher - finds a Python that has tkinter and starts the app.
setlocal
set "HERE=%~dp0"
set "PYEXE="

rem 1) a virtualenv sitting next to this file
if exist "%HERE%.venv\Scripts\pythonw.exe" set "PYEXE=%HERE%.venv\Scripts\pythonw.exe"

rem 2) the Python runtime bundled with DeepSeek Harness on this machine
if not defined PYEXE (
    if exist "%USERPROFILE%\.dsh\dsh-runtimes\dsh-primary-runtime\dependencies\python\pythonw.exe" (
        set "PYEXE=%USERPROFILE%\.dsh\dsh-runtimes\dsh-primary-runtime\dependencies\python\pythonw.exe"
    )
)

rem 3) the official Windows launcher
if not defined PYEXE (
    where py >nul 2>nul
    if not errorlevel 1 set "PYEXE=py -3"
)

rem 4) plain python on PATH (last resort)
if not defined PYEXE (
    where python >nul 2>nul
    if not errorlevel 1 set "PYEXE=python"
)

if not defined PYEXE (
    echo No Python found. Install Python 3.10+ and run: python -m glythminis
    pause
    exit /b 1
)

pushd "%HERE%"
start "GlythMinis" %PYEXE% -m glythminis %*
popd
