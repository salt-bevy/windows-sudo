# One-time setup for testing this tool inside Windows Sandbox instead of on a
# real machine's registry. Enables the "Containers-DisposableClientVM" feature
# that Windows Sandbox needs, then reports whether a restart is required
# (Windows Sandbox.exe won't exist until you restart, even when the feature
# itself already reports "Enabled").
#
# Usage:
#     powershell -File enable_sandbox.ps1

$isAdmin = ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole(
    [Security.Principal.WindowsBuiltinRole]::Administrator)
if (-not $isAdmin) {
    Write-Host 'Elevation is required -- requesting it now...'
    $proc = Start-Process powershell -Verb RunAs -ArgumentList @(
        '-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', $PSCommandPath
    ) -PassThru -Wait
    exit $proc.ExitCode
}

$feature = Get-WindowsOptionalFeature -Online -FeatureName Containers-DisposableClientVM -ErrorAction SilentlyContinue

if ($feature -and $feature.State -eq 'Enabled') {
    Write-Host 'Containers-DisposableClientVM is already enabled.'
} else {
    Write-Host 'Enabling Containers-DisposableClientVM (Windows Sandbox)...'
    Enable-WindowsOptionalFeature -Online -FeatureName Containers-DisposableClientVM -All -NoRestart | Out-Null
}

$rebootPending = Test-Path 'HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Component Based Servicing\RebootPending'
if ($rebootPending -or -not (Test-Path "$env:ProgramFiles\Windows Sandbox\WindowsSandbox.exe")) {
    Write-Host ''
    Write-Host 'A restart is required before "Windows Sandbox" will actually run.'
    Write-Host 'Restart, then launch windows-sudo-test.wsb to test this tool in a disposable VM.'
} else {
    Write-Host 'No restart needed -- Windows Sandbox is ready to use.'
}

Read-Host 'Press Enter to close'
