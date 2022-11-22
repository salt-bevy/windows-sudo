# windows-sudo
Like the Linux "sudo" command, but for Windows. Uses Python and pywin32 to run Administrator code.

### Installation

1. Install [Python 3](https://www.python.org/downloads/) using **for all users** and .
2. `py -m pip install pywin32 pyyaml`
3. `install_sudo.bat`
4. Log off and back on, to make .py files valid path extensions. Until then, use explicit "sudo.py".

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

Environment variables "PATH" and "PATHEXT" are a special case, and append their argument to the path. So, to add "C:\Salt" to the search path, use . . .

`sudo --set-system-env="PATH: C:\Salt"`

To remove items from the PATH or PATHEXT, prepend the name with a dash . . .

`sudo --set-system-env="PATH -C:\Salt"`

For lazy systems administrators who use [Salt](https://saltproject.io/), 
any command beginning with "salt-" will be run with a pause . . .

`sudo salt-call --local test.version`

Last of all, sudo.py installs itself.

    cd <the windows-sudo root directory>\code
    py sudo.py --install-sudo-command`
