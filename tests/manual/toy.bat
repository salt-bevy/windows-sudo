@echo off
REM Toy script for interactively testing "sudo".
REM Usage:
REM     sudo tests\manual\toy.bat

echo cwd: %CD%
echo args: %*
net session >nul 2>&1
if %errorlevel% == 0 (
    echo Elevated: True
) else (
    echo Elevated: False
)
pause
