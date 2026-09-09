# pywin32/pyyaml are what sudo.py itself needs (see the ImportError in
# windows_sudo/sudo.py) -- pip.installed alone isn't enough for pywin32,
# it also needs its postinstall step to register the DLLs, which pip
# never runs on its own.

pywin32_and_pyyaml:
  pip.installed:
    - pkgs:
      - pywin32
      - pyyaml
    - require:
      - chocolatey: python

pywin32_postinstall:
  cmd.run:
    - name: pywin32_postinstall.exe -install
    - unless: python -c "import win32api"
    - require:
      - pip: pywin32_and_pyyaml
