@echo off
setlocal EnableExtensions DisableDelayedExpansion
title Hover Dict Launcher
set "PYTHONUTF8=1"

pushd "%~dp0" || goto folder_error
set "HD_APP=hover_dict_v5_1_LN_fix.py"

if not exist "%HD_APP%" (
    echo [LOI] Khong tim thay %HD_APP%.
    echo Dat file .bat cung thu muc voi file .py, roi bam dup lai.
    goto failed
)

call :find_python
if not defined HD_PY (
    echo [LOI] Khong tim thay Python 3.12 x64 kem Tkinter.
    echo Chay Check_And_Install.bat truoc.
    goto failed
)

if /i "%~1"=="settings" goto settings

rem Only start Chrome for the app's default local DeepL Web configuration.
findstr /b /r /c:"TRANSLATE_BACKEND[ ]*=[ ]*.deepl_web." "%HD_APP%" >nul
if errorlevel 1 goto run
findstr /b /c:"DEEPL_WEB_CDP_URL" "%HD_APP%" | findstr /l /c:"http://127.0.0.1:9222" >nul
if errorlevel 1 goto run

call :cdp_ready
if not errorlevel 1 goto run

set "HD_CHROME="
if exist "%ProgramFiles%\Google\Chrome\Application\chrome.exe" set "HD_CHROME=%ProgramFiles%\Google\Chrome\Application\chrome.exe"
if not defined HD_CHROME if exist "%ProgramFiles(x86)%\Google\Chrome\Application\chrome.exe" set "HD_CHROME=%ProgramFiles(x86)%\Google\Chrome\Application\chrome.exe"
if not defined HD_CHROME if exist "%LocalAppData%\Google\Chrome\Application\chrome.exe" set "HD_CHROME=%LocalAppData%\Google\Chrome\Application\chrome.exe"
if not defined HD_CHROME for /f "delims=" %%G in ('where chrome.exe 2^>nul') do if not defined HD_CHROME set "HD_CHROME=%%G"
if not defined HD_CHROME (
    echo [CANH BAO] Khong tim thay Chrome. Hover Dict van se duoc mo.
    goto run
)

echo Dang mo Chrome rieng cho DeepL Web...
start "" "%HD_CHROME%" --remote-debugging-port=9222 --user-data-dir="%CD%\BotChromeProfile" "https://www.deepl.com/en/translator"
for /l %%I in (1,1,12) do (
    call :cdp_ready
    if not errorlevel 1 goto run
    timeout /t 1 /nobreak >nul
)
echo [CANH BAO] Chrome chua san sang o cong 9222. Hover Dict van se duoc mo.

:run
"%HD_PY%" "%HD_APP%"
set "HD_EXIT=%errorlevel%"
goto finished

:settings
"%HD_PY%" "%HD_APP%" --settings
set "HD_EXIT=%errorlevel%"

:finished
popd
echo.
echo Hover Dict da thoat. Neu co loi, xem thong bao o tren.
pause
exit /b %HD_EXIT%

:failed
popd
pause
exit /b 1

:folder_error
echo [LOI] Khong mo duoc thu muc chua launcher.
pause
exit /b 1

:cdp_ready
"%HD_PY%" -c "import http.client,json,sys; c=http.client.HTTPConnection('127.0.0.1',9222,timeout=0.6); c.request('GET','/json/version'); r=c.getresponse(); sys.exit(0 if r.status==200 and json.load(r).get('webSocketDebuggerUrl') else 1)" >nul 2>&1
exit /b %errorlevel%

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
