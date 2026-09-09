# Run this manually inside a fresh Windows Sandbox (or VM) to get everything
# sudo.py needs. Installs Chocolatey, then Python + pywin32/pyyaml via choco
# and pip, and runs pywin32's required postinstall step -- all with PATH
# picked up correctly in this same session (no "restart the shell" dance).
#
# Chocolatey is also there afterward for anything else you want to pull in
# ad hoc while testing.
#
# Usage (inside the sandbox, from C:\windows-sudo):
#     powershell -ExecutionPolicy Bypass -File sandbox\bootstrap.ps1

Set-ExecutionPolicy Bypass -Scope Process -Force
[System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072
Invoke-Expression ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))

# The installer updates PATH in the registry but not this running process --
# reload it so 'choco', then 'python'/'pip', resolve without a new shell.
$env:ChocolateyInstall = Convert-Path "$env:ProgramData\chocolatey"
Import-Module "$env:ChocolateyInstall\helpers\chocolateyProfile.psm1"
refreshenv

choco install -y python
refreshenv

python -m pip install --quiet --no-warn-script-location pywin32 pyyaml
pywin32_postinstall.exe -install

Write-Host ''
Write-Host 'Bootstrap complete -- python, pip, choco, pywin32, and pyyaml are all on PATH.'
Write-Host 'Next: python windows_sudo\sudo.py --install-sudo-command'
