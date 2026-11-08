@echo off
setlocal EnableExtensions DisableDelayedExpansion
title Hover Dict - Check and Install
set "PYTHONUTF8=1"
pushd "%~dp0" || goto folder_error
if not exist "hover_dict_v5_1_LN_fix.py" (
    echo [ERROR] Put this BAT beside hover_dict_v5_1_LN_fix.py.
    goto failed
)
call :find_python
if defined HD_PY goto check
where winget.exe >nul 2>&1
if errorlevel 1 (
    echo [MISSING] Python 3.12 x64 and WinGet.
    echo Install Python 3.12 from https://www.python.org/downloads/windows/
    echo Include Python Launcher and Tcl/Tk, then run this BAT again.
    goto failed
)
echo [INSTALL] Python 3.12 x64...
winget install --id Python.Python.3.12 --exact --source winget --architecture x64 --scope user --silent --accept-package-agreements --accept-source-agreements
call :find_python
if not defined HD_PY (
    echo [ERROR] Python 3.12 x64 is not ready. Check the install message above.
    echo Close this CMD, then open Check_And_Install.bat again.
    goto failed
)
:check
"%HD_PY%" "hover_dict_v5_1_LN_fix.py" --setup
set "HD_EXIT=%errorlevel%"
popd
echo.
pause
exit /b %HD_EXIT%
:failed
popd
pause
exit /b 1
:folder_error
echo [ERROR] Cannot open the app folder.
pause
exit /b 1

:find_python
set "HD_PY="
for /f "delims=" %%P in ('py -3.12 -c "import sys,struct,tkinter; assert sys.version_info[:2]==(3,12) and struct.calcsize('P')==8; print(sys.executable)" 2^>nul') do set "HD_PY=%%P"
if defined HD_PY exit /b 0
for %%P in ("%LocalAppData%\Programs\Python\Python312\python.exe" "%ProgramFiles%\Python312\python.exe") do if not defined HD_PY if exist "%%~P" (
    "%%~P" -c "import sys,struct,tkinter; sys.exit(0 if sys.version_info[:2]==(3,12) and struct.calcsize('P')==8 else 1)" >nul 2>&1
    if not errorlevel 1 set "HD_PY=%%~P"
)
if not defined HD_PY exit /b 1
exit /b 0
