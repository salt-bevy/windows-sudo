# Runs this project's own installer. Note: sudo.py's UAC self-elevation
# (see windows_sudo/sudo.py's runAsAdmin call) still opens a separate
# elevated console that this state's stdin can't reach -- accepting that
# UAC prompt, and its "Hit <Enter> to continue" pause, stays a manual step
# in the VM console even when the rest of this run is unattended. The
# `stdin` below only answers the first, non-elevated "native sudo found"
# prompt.

install_sudo_command:
  cmd.run:
    - name: python windows_sudo\sudo.py --install-sudo-command
    - cwd: {{ pillar['windows_sudo']['repo_dir'] }}
    - stdin: "y\n"
    - require:
      - cmd: pywin32_postinstall
