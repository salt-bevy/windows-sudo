# Toy script for interactively testing "sudo".
# Usage:
#     sudo --powershell ".\tests\manual\toy.ps1"

$elevated = ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole(
    [Security.Principal.WindowsBuiltinRole]::Administrator)

Write-Host "PID:" $PID
Write-Host "cwd:" (Get-Location)
Write-Host "args:" $args
Write-Host "Elevated:" $elevated
Read-Host "Press Enter to exit"
