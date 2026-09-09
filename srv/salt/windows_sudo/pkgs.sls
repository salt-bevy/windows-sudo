# Chocolatey + Python. Salt's own chocolatey.bootstrap installs Chocolatey
# itself (idempotent -- skipped once chocolatey.chocolatey_version succeeds),
# then chocolatey.installed pulls Python the same way "choco install python"
# would, but through Salt so it's part of the same state run instead of a
# separately-run script.

chocolatey_bootstrap:
  module.run:
    - name: chocolatey.bootstrap
    - unless:
      - fun: chocolatey.chocolatey_version

python:
  chocolatey.installed:
    - require:
      - module: chocolatey_bootstrap
