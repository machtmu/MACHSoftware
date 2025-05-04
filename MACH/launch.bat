@echo off
echo.
echo Select an option:
echo   1: Launch server and Labjack
echo   2: Launch server, GUI, and LabJack
echo   3: Launch server and run custom Python file
echo.
set /p choice="Enter option (1, 2, or 3): "

if "%choice%"=="1" goto Option1
if "%choice%"=="2" goto Option2
if "%choice%"=="3" goto Option3

echo Invalid choice.
goto End

:Option1
echo Launching server and GUI in MACHNET...
start cmd /k "cd /d %~dp0\MACHNET && go run server.go"
start cmd /k "cd /d %~dp0\MACHX && labjack_test.exe"
goto End

:Option2
echo Launching server and GUI in MACHNET, and LabJack in MACHX...
set /p pyfile="Enter Python file name (with extension): "
start cmd /k "cd /d %~dp0\MACHNET && go run server.go"
start cmd /k "cd /d %~dp0\MACHNET && py %pyfile%"
timeout /t 2 /nobreak >nul
start cmd /k "cd /d %~dp0\MACHX && labjack_test.exe"
goto End

:Option3
echo Launching server in MACHNET and running custom Python file...
set /p pyfile="Enter Python file name (with extension): "
start cmd /k "cd /d %~dp0\MACHNET && go run server.go"
start cmd /k "cd /d %~dp0\MACHNET && py %pyfile%"
goto End

:End
echo.
echo Done.
pause
