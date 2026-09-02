# windows-sudo
Like the Linux "sudo" command, but for Windows. Uses Python and pywin32 to run Administrator code.

### Installation

1. Install [Python 3](https://www.python.org/downloads/) using **for all users** and .
2. `py -m pip install pywin32 pyyaml`
3. `install_sudo.bat`
4. Log off and back on, to make .py files valid path extensions. Until then, use explicit "sudo.py".

Alternatively, install the package from PyPI (`pip install windows-sudo`) and run
`py -m windows_sudo.sudo --install-sudo-command` in place of steps 2-3 above.

### Operation

Usually . . .
`sudo your command here`

If you are forgetful . . . `sudo --help` or `sudo /?`

To get an interactive Administrator session . . .

`sudo cmd` or `sudo bash`

To pause the Administrator window so you can read the messages before they disappear. . .

`sudo --pause your command here`

### Special commands

To edit the goofy Windows version of /etc/hosts . . .

`sudo --hosts`

To set environment variables from the command line . . .

`sudo --set-user-env="arg1: val1, arg2: val2"`

or

`sudo --set-system-env="arg1: val1, arg2: val2"`

(the above argument strings are in YAML format, and must be quoted because the spaces
are part of the syntax.)

To remove environment variables . . .

`sudo --set-user-env="arg: None"`

Environment variables "PATH" and "PATHEXT" are a special case, and append their argument to the path. So, to add "C:\Some\Directory" to the search path, use . . .

`sudo --set-system-env="PATH: C:\Some\Directory"`

To remove items from the PATH or PATHEXT, prepend the name with a dash . . .

`sudo --set-system-env="PATH -C:\Some\Directory"`

For lazy systems administrators who use [Salt](https://saltproject.io/), 
any command beginning with "salt-" will be run with a pause . . .

`sudo salt-call --local test.version`

Last of all, sudo.py installs itself.

    cd <the windows-sudo root directory>\windows_sudo
    py sudo.py --install-sudo-command`

### Windows 11 note

Recent Windows 11 builds (24H2+) can ship their own native `sudo` command in
`System32`, which is normally found ahead of this package's version. When you
run `--install-sudo-command`, it now detects that case and offers to move this
package's install directory to the front of your PATH so `sudo` keeps
resolving to this package instead. Answer "n" to leave the native command in
control.
