# windows-sudo
Like the Linux "sudo" command, but for Windows. Uses Python and pywin32 to run Administrator code.

Each command will present a User Account Control prompt to elevate the privilege for that command.

You can also launch an interactive  Command (cmd), bash, or PowerShell window.

The command will execute in the current directory (unlike Window's sudo.exe.)

(This will, theoretically, also actually run on Linux: but what would be the point?)

### Installation

1. Install [Python 3](https://www.python.org/downloads/) (either **for all users** or **single user**) and .
2. `pip install windows-sudo`
3. `windows-sudo-install`
4. Answer "Y" to the query about modifying PATH.

   (pip will install the `windows-sudo-install` command automatically as part of step 2 -- but it can't
   *run* it for you, since a `pip install` from a prebuilt wheel never executes
   arbitrary code, only `windows-sudo-install` itself can. It will request elevatation when needed.)
4. Open a new cmd window -- `sudo` works there immediately (it installs a `sudo.bat`
   launcher, so no `.py` file association or PATHEXT change is needed). The one
   exception: if it just moved the native Windows `sudo.exe` on the system PATH (see
   the Windows 11 note below), log off and back on for *that* change to take effect
   everywhere.

Alternatively, to run from a source checkout instead: `py -m pip install pywin32
pyyaml`, then `install_sudo.bat` in place of steps 2-3 above.

During installation, it will offer to move the Python script directory in PATH ahead of the directory which contains
Windows 11 *sudo.exe*. If you do not select that option, you will always need to type `sudo.bat`
in order to run this utility.
IMHO, this one has much better features.

### Operation

Usually . . .
`sudo your command here`

If you are forgetful . . . `sudo --help` or `sudo /?`

To get an interactive Administrator session . . .

`sudo cmd`, `sudo bash`, or `sudo ps` (PowerShell)

To pause the Administrator window so you can read the messages before they disappear. . .

`sudo --pause your command here`

### Special commands

To edit the hard-to-find Windows version of /etc/hosts . . .

`sudo --hosts`

To permanently set environment variables from the command line . . .

`sudo --set-user-env="arg1: val1, arg2: val2"`

or

`sudo --set-system-env="arg1: val1, arg2: val2"`

(the above argument strings are in YAML format, and must be quoted because the spaces
are part of the syntax.)

To remove an environment variable entirely, set its value to "None" . . .

`sudo --set-user-env="arg: None"`

Environment variables "PATH" and "PATHEXT" are a special case, and append their argument to the path. So, to add "C:\Some\Directory" to the search path, use . . .

`sudo --set-system-env="PATH: C:\Some\Directory"`

To remove one item from PATH or PATHEXT specifically (leaving the rest of the
list alone), prepend a dash to its *value*, not its name . . .

`sudo --set-system-env="PATH: -C:\Some\Directory"`

Note the two dash forms are not interchangeable: `"PATH: -C:\Some\Directory"`
removes just that one entry from the PATH list, while `"arg: None"` deletes
the whole "arg" variable. A leading dash on the variable *name* itself (e.g.
`"-arg: val"`) is not special -- it is taken literally, as part of the name.

For lazy systems administrators who use [Salt](https://saltproject.io/), 
any command beginning with "salt-" will be run with a pause . . .

`sudo salt-call --local test.version`

Or as a short cut, "--salt" will expand to "salt-call --local", so:

`sudo --salt test.version`

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

### Testing

An automated go/no-go suite covers everything that needs no elevation
(CLI smoke tests, arg parsing, quoting, etc.) . . .

`py -m pytest tests/`

For the elevated behavior itself, which only a human can judge, some toy
scripts are provided for interactive testing under `sudo` . . .

    sudo tests\manual\toy.py
    sudo tests\manual\toy.bat
    sudo --powershell ".\tests\manual\toy.ps1"

Each one reports its working directory, arguments, and whether it ended up
elevated, then waits for a keypress so you can read the result.
