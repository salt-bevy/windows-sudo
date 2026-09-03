#!/usr/bin/env python
# -*- coding: utf-8; mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vim: fileencoding=utf-8 tabstop=4 expandtab shiftwidth=4

# (C) COPYRIGHT © Preston Landers 2010
# Released under the same license as Python 2.6.5
#
# Python3 update and extensive changes by: Vernon Cole 2018, 2019, 2020, 2026

import sys, os, traceback, time, subprocess, shutil

if os.name == 'nt':
    try:
        # noinspection PyUnresolvedReferences
        import winreg, win32gui, win32con, win32event, win32process
        # noinspection PyUnresolvedReferences
        from win32com.shell import shell, shellcon
        # noinspection PyUnresolvedReferences
        from win32com.shell.shell import ShellExecuteEx
    except ImportError:
        raise ImportError('PyWin32 module import failure.  Try "py -m pip install pywin32 pyyaml".')

try:
    # imported as part of the windows_sudo package (e.g. under pytest)
    from .argv_quote import quote
except ImportError:
    # run as a standalone script, e.g. the flat copy installed onto PATH
    # noinspection PyUnresolvedReferences
    from argv_quote import quote

try:
    # noinspection PyUnresolvedReferences
    import yaml as decoder
    def loader(s):
        return decoder.load(s, decoder.Loader)
    encoder = decoder.dump
    decodeError = decoder.YAMLError
except (ModuleNotFoundError, ImportError):
    # noinspection PyUnresolvedReferences
    import json as decoder
    loader = decoder.loads
    encoder = decoder.dumps
    decodeError = decoder.JSONDecodeError
    print('NOTE: no YAML module found, falling back to JSON. Try "pip install pyyaml".')

__version__ = '2.0.0.rc4'

ELEVATION_FLAG = "--_context"  # internal use only. Should never be passed on a user command line
PREPEND_PATH_FLAG = "--_prepend-native-sudo-path"  # internal use only, see warn_if_native_sudo()

def has_context():  # we-were-here flag has been set
    '''
    Do command line arguments include one beginning with "--_context"?
    :return: bool, context flag was present in argv
    '''
    return any(arg.startswith(ELEVATION_FLAG) for arg in sys.argv)


def isUserAdmin():
    '''
    Checks for "--_context" argument or OS opinion of whether current process is elevated
    :return: bool, process has administrator privileges.
    '''
    if has_context():
        return True
    if os.name == 'nt':
        try:
            return shell.IsUserAnAdmin()
        except Exception as e:
            traceback.print_exc()
            print("Admin check failed, assuming not an admin.")
            return False
    elif os.name == 'posix':
        # Check for root on Posix
        return os.getuid() == 0
    else:
        raise RuntimeError("Unsupported operating system for this module: {}".format(os.name))


def runAsAdmin(commandLine=None, context=None, python_shell=False, wait=True):
    '''
    Run a command with elevated system privileges.

    :param commandLine: str . a string, or sequence of strings, of the command line
    :param context: dic or bool. additional context to pass to the elevated program. Adds CLI argument "--_context={}"
    :param python_shell: bool, the command is a Python script.
    :param wait: bool, wait for command completion. If False, will run the command asynchronously.
    :return: int, the return code from the execution. Will be None for async, 89 for some Windows error conditions.
    '''
    if commandLine is None:
        cmdLine = []
    elif isinstance(commandLine, str):
        cmdLine = commandLine.split()
    else:
        if not isinstance(commandLine, (tuple, list)):
            raise ValueError("commandLine must be a sequence or a string.")
        cmdLine = list(commandLine)  # make a local copy

    if python_shell:
        python_exe = sys.executable  # the path to the running Python image file
        cmdLine.insert(0, python_exe)  # run the Python command with elevation.

    if isinstance(context, dict):
        ctx = encoder(context)
        cmdLine.append(ELEVATION_FLAG + "=" + ctx)
    elif context:
        cmdLine.append(ELEVATION_FLAG)

    if os.name == 'posix':
        cmdLine.insert(0, "sudo")  # make a call using the system's "sudo"
        cmd = quote(*cmdLine)
        print('(Running command-->', cmd, ')')
        return_code = subprocess.call(cmd, shell=True)

    elif os.name == 'nt':  # running Windows -- must use pywin32 to ask for elevation
        showCmd = win32con.SW_SHOWNORMAL
        try:
            params = quote(*cmdLine[1:])
        except IndexError:
            params = ""
        try:
            cmd = quote(cmdLine[0])
        except IndexError:
            cmd = "_No_command_was_supplied_"
        lpVerb = 'runas'  # causes UAC elevation prompt.
        print()
        if wait:
            print("This window will be waiting while a child window is run as an Administrator...")
        print("(Running command-->{} {})".format(cmd, params))
        procInfo = ShellExecuteEx(nShow=showCmd,
                                  fMask=shellcon.SEE_MASK_NOCLOSEPROCESS,
                                  lpVerb=lpVerb,
                                  lpParameters=params,
                                  lpFile=cmd)
        if wait:
            procHandle = procInfo['hProcess']
            if procHandle is None:
                print("Windows Process Handle is Null. RunAsAdmin did not create a child process.")
                return_code = 89  # Windows ERROR_NO_PROC_SLOTS
            else:
                win32event.WaitForSingleObject(procHandle, win32event.INFINITE)
                return_code = win32process.GetExitCodeProcess(procHandle)
                # print("Process handle %s returned code %s" % (procHandle, return_code))
                procHandle.Close()
                print("(Now Returned from waiting...)")
        else:
            return_code = None  # asked not to wait for completion
    else:
        raise RuntimeError("Unsupported operating system for this module: {}".format(os.name))
    return return_code


def get_context(flag=ELEVATION_FLAG):
    '''
    parse and return json dictionary from the --_context= argument.
    A stray unquoted space in the value (e.g. --set-user-env='a': 'b','c':'d' typed
    without an enclosing outer quote) makes the shell split it across multiple argv
    entries -- rejoin everything from the flagged argument onward before parsing, so
    only a quoting mistake around the OUTER quotes is fatal, not one around an inner value.
    :return: dic
    '''
    for i, arg in enumerate(sys.argv):
        if arg.startswith(flag):
            try:
                ctx = ' '.join([arg] + sys.argv[i + 1:]).split('=', 1)[1]
                if not ctx.startswith('{'):
                    ctx = '{' + ctx
                if not ctx.endswith('}'):
                    ctx += '}'
                ret = loader(ctx)
                return ret
            except (IndexError, decodeError) as e:
                print("Decode Error in {}=>{}".format(flag, e))
                print("sys.argv-->", sys.argv)
                return {}
    return {}


def set_env_variables_permanently_win(key_value_pairs, whole_machine = False):
    """
    Similar to os.environ[var_name] = var_value for all pairs provided, but instead of setting the variables in the
    current process, sets the environment variables permanently at the os MACHINE level.
    NOTE:  process must be "elevated" before making this call.  Use "sudo" first.

    Original Recipe from http://code.activestate.com/recipes/416087/
    :param key_value_pairs: a dictionary of variable name+value to set
    :param whole_machine: if True the env variables will be set at the MACHINE (HKLM) level.
           If False it will be done at USER level (HKCU)
    :return:
    """
    if not isinstance(key_value_pairs, dict):
        raise ValueError('{!r} must be {}'.format(key_value_pairs, dict))
    if os.name != 'nt':
        raise ModuleNotFoundError('Attempting Windows operation on non-Windows')

    subkey = r'SYSTEM\CurrentControlSet\Control\Session Manager\Environment' if whole_machine \
        else r'Environment'

    with winreg.OpenKeyEx(winreg.HKEY_LOCAL_MACHINE if whole_machine else winreg.HKEY_CURRENT_USER,
                          subkey, 0, winreg.KEY_ALL_ACCESS) as key:
        for name, value in key_value_pairs.items():
            try:
                if value.lower() == "none":
                    value = None
            except AttributeError:
                pass
            print('  setting environment variable -->', name, '=', value)
            try:
                present, value_type = winreg.QueryValueEx(key, name)
            except OSError:
                present = ''
                value_type = winreg.REG_SZ if isinstance(value, str) else \
                    winreg.REG_BINARY if isinstance(value, bool) else winreg.REG_DWORD
            repaired_missing = []
            if not whole_machine and name.upper() == 'PATHEXT':
                # Unlike PATH, Windows does NOT concatenate the user and system PATHEXT --
                # a user-level PATHEXT completely replaces the system one. Fold in any system
                # extensions the user-level value is missing (whether it was empty, or was
                # already reduced to just our own past addition) so we never leave the user
                # with a PATHEXT that lacks .EXE/.BAT/.CMD/etc. and breaks their CLI.
                try:
                    with winreg.OpenKeyEx(
                            winreg.HKEY_LOCAL_MACHINE,
                            r'SYSTEM\CurrentControlSet\Control\Session Manager\Environment',
                            0, winreg.KEY_READ) as system_key:
                        system_present, _ = winreg.QueryValueEx(system_key, name)
                except OSError:
                    system_present = ''
                have = {e.upper() for e in present.split(';') if e}
                repaired_missing = [e for e in system_present.split(';') if e and e.upper() not in have]
                if repaired_missing:
                    present = ';'.join([e for e in present.split(';') if e] + repaired_missing)
                    print('Repairing {} -- restoring missing system extension(s): {}'.format(
                        name, ', '.join(repaired_missing)))
            print('old value was {} = {}'.format(name, present))
            if name.upper() in ['PATH', 'PATHEXT']:
                elements = [e for e in present.upper().split(';') if e]
                case_elements = [e for e in present.split(';') if e]
                if value.startswith('-'):  # remove a path element
                    value = value[1:]  # remove the '-'
                    try:
                        indx = elements.index(value.upper())
                        removed = case_elements.pop(indx)
                        print('Removing "{}" from {}'.format(removed, name))
                    except ValueError:
                        print('Element "{}" was not found in {}'.format(value, name))
                        continue
                else:  # adding a path element
                    if value.upper() in elements and not repaired_missing:
                        print('Value {} already in {}'.format(value, present))
                        continue
                    elif value.upper() in elements:
                        pass  # already present, but still need to write back the repaired value
                    else:
                        print('"{}" will not be entirely changed. "{}" will be appended at the end.'.format(
                            name, value))
                        case_elements.append(value)
                value = ';'.join(case_elements)
            if value is not None:
                print("Setting ENVIRONMENT VARIABLE '{}' to '{}'".format(name, value))
                winreg.SetValueEx(key, name, 0, value_type, value)
            else:
                try:
                    winreg.DeleteValue(key, name)
                    print("Deleting ENV VARIABLE '{}'".format(name))
                except FileNotFoundError:
                    print("ENV VARIABLE '{}' was not present".format(name))

    # tell all the world that a change has been made
    win32gui.SendMessageTimeout(win32con.HWND_BROADCAST, win32con.WM_SETTINGCHANGE, 0, 'Environment',
                                win32con.SMTO_ABORTIFHUNG, 1000)
    if has_context():
        input('Hit <Enter> to continue . . .')


def user_python_scripts_dir():
    '''
    A "for me only" (single-user) Python install adds its own "Scripts" directory to the
    current user's PATH, and that directory is already writable without elevation. An
    "all users" install instead goes under Program Files and needs admin rights to touch.

    :return: str or None. The Scripts directory next to the running interpreter, when this
             looks like a per-user install, else None.
    '''
    if os.name != 'nt':
        return None
    local_app_data = os.environ.get('LOCALAPPDATA')
    if not local_app_data:
        return None
    exe_dir = os.path.dirname(os.path.abspath(sys.executable))
    if not os.path.normcase(exe_dir).startswith(os.path.normcase(local_app_data)):
        return None  # not a per-user install (e.g. Program Files, or a venv)
    scripts_dir = os.path.join(exe_dir, 'Scripts')
    return scripts_dir if os.path.isdir(scripts_dir) else None


def native_sudo_path():
    '''
    Windows 11 (24H2+) can ship its own built-in "sudo.exe" in System32, which will shadow
    this package's "sudo" command because System32 is searched before C:\\Windows.
    :return: str, path to the native sudo.exe, whether or not it actually exists.
    '''
    system_root = os.environ.get('SystemRoot', r'C:\Windows')
    return os.path.join(system_root, 'System32', 'sudo.exe')


def native_sudo_present():
    '''
    :return: bool, True if a native Windows "sudo" command is installed on this machine.
    '''
    return os.name == 'nt' and os.path.isfile(native_sudo_path())


def already_ahead_of_native_sudo(install_dir):
    '''
    Check the PERMANENT system PATH (not os.environ, which won't reflect a change made
    earlier in the same login session) to see whether `install_dir` already precedes the
    native sudo.exe's directory, so we don't keep re-warning/re-prompting about a fight
    that was already won on a previous run.

    :param install_dir: str, the directory this package's sudo.py is installed into.
    :return: bool, True if `install_dir` is already ahead of native sudo's directory on
             the system PATH.
    '''
    try:
        with winreg.OpenKeyEx(winreg.HKEY_LOCAL_MACHINE,
                              r'SYSTEM\CurrentControlSet\Control\Session Manager\Environment',
                              0, winreg.KEY_READ) as key:
            current, _ = winreg.QueryValueEx(key, 'PATH')
    except OSError:
        return False
    # raw registry values may contain unexpanded references like "%SystemRoot%\system32"
    elements = [os.path.normcase(os.path.normpath(os.path.expandvars(e)))
                for e in current.split(';') if e]
    target = os.path.normcase(os.path.normpath(install_dir))
    native_dir = os.path.normcase(os.path.normpath(os.path.dirname(native_sudo_path())))
    try:
        return elements.index(target) < elements.index(native_dir)
    except ValueError:
        return False


def prepend_path_win(directory, whole_machine=True):
    '''
    Move `directory` to the very front of the permanent PATH, so it is searched before
    other entries such as C:\\Windows\\System32. Any existing occurrence of `directory`
    is removed first, so repeated calls do not pile up duplicates.
    NOTE: process must be "elevated" before making this call when whole_machine=True.

    :param directory: str, the directory to move to the front of PATH.
    :param whole_machine: bool, if True modify the system (HKLM) PATH, else the user (HKCU) PATH.
    :return:
    '''
    if os.name != 'nt':
        raise ModuleNotFoundError('Attempting Windows operation on non-Windows')

    subkey = r'SYSTEM\CurrentControlSet\Control\Session Manager\Environment' if whole_machine \
        else r'Environment'
    hive = winreg.HKEY_LOCAL_MACHINE if whole_machine else winreg.HKEY_CURRENT_USER

    with winreg.OpenKeyEx(hive, subkey, 0, winreg.KEY_ALL_ACCESS) as key:
        try:
            current, value_type = winreg.QueryValueEx(key, 'PATH')
        except OSError:
            current, value_type = '', winreg.REG_EXPAND_SZ
        target = os.path.normcase(os.path.normpath(directory))
        elements = [e for e in current.split(';') if e and os.path.normcase(os.path.normpath(e)) != target]
        elements.insert(0, directory)
        new_path = ';'.join(elements)
        winreg.SetValueEx(key, 'PATH', 0, value_type, new_path)
    print('Moved "{}" to the front of the {} PATH.'.format(directory, 'system' if whole_machine else 'user'))

    # tell all the world that a change has been made
    win32gui.SendMessageTimeout(win32con.HWND_BROADCAST, win32con.WM_SETTINGCHANGE, 0, 'Environment',
                                win32con.SMTO_ABORTIFHUNG, 1000)


def warn_if_native_sudo(install_dir):
    '''
    If a native Windows "sudo" is present, warn the user and offer to move `install_dir`
    ahead of it on the PATH, so this package's "sudo" command wins instead. Moving it
    requires elevation (it edits the system PATH); if we're not already elevated, we
    relaunch ourselves with a UAC prompt to finish the job in this one step, rather than
    telling the user to go re-run the installer as Administrator themselves.
    :param install_dir: str, the directory this package's sudo.py was just installed into.
    :return:
    '''
    if not native_sudo_present():
        return
    if already_ahead_of_native_sudo(install_dir):
        return
    native_path = native_sudo_path()
    print()
    print('WARNING: A native Windows "sudo" command was found at "{}".'.format(native_path))
    print('The system PATH (which includes System32) is always searched before the user')
    print('PATH, so the built-in sudo will normally run instead of this package\'s version')
    print('when you type "sudo" -- even if "{}" is on your own PATH.'.format(install_dir))
    try:
        answer = input('Put this "windows-sudo" version ahead of the native one on the system PATH? [y/N] ')
    except EOFError:
        answer = 'n'
    if not answer.strip().lower().startswith('y'):
        print('Leaving PATH unchanged. The native "sudo" will take precedence over this package.')
        return
    if isUserAdmin():
        prepend_path_win(install_dir, whole_machine=True)
    else:
        print('Elevation is required to modify the system PATH -- requesting it now...')
        runAsAdmin([os.path.abspath(__file__), PREPEND_PATH_FLAG + '=' + install_dir], python_shell=True)


def main():
    if len(sys.argv) == 1 or sys.argv[1] in ["--help", "-h", "su", "/?", "/help"]:
        print(r'''usage:
         sudo <command> <arguments> # will run <command> with elevated priviledges
         sudo --pause <cmd> <args>  # will keep the command screen open until you hit a key
         sudo salt-xxx <cmd> . . .  # will call salt-xxx (from wherever it's installed) and then pause
         sudo --set-user-env="'arg1': 'val1','arg2': 'val2'" # adds values to the user's PERMANENT environment vars
         sudo --set-system-env="arg1: val1, arg2: val2" # adds values to the system's PERMANENT environment vars
            (note: "PATH" and "PATHEXT" args are special. "val" adds a path element. "-val" removes it.)
            (For other environment variables, use "'<variable_name>': None" to delete it.)
         sudo --hosts  # will open your /etc/hosts file for editing (at the weird Windows location)
         sudo --powershell <command>  # runs <command> in an elevated PowerShell window (stays open)
         sudo --install-sudo-command  # create a runnable copy of itself in C:\Windows
         sudo bash # starts an Administrator Linux-Subsystem-for-Windows window
         sudo cmd  # starts an Administrator command window
         sudo ps   # starts an Administrator PowerShell window
         ''')
    elif sys.argv[1] == "--version":
        print('sudo version', __version__)
    elif sys.argv[1] == "--hosts":
        print('....... NEXT, a useful example ... editing the "etc/hosts" file ........')
        if os.name == 'nt':
            call = ["notepad", r"C:\Windows\System32\drivers\etc\hosts"]
        else:
            call = ['nano', '/etc/hosts']
        runAsAdmin(call)
    elif sys.argv[1] == "--powershell" and os.name == 'nt':
        # takes the whole remainder of the command line as one PowerShell command, rather
        # than routing through sudo_cd.bat -- batch's own quote-handling mangles a command
        # string with embedded spaces/quotes long before PowerShell ever sees it.
        command_str = ' '.join(sys.argv[2:])
        if not command_str:
            print('usage: sudo --powershell <command>')
        else:
            print('Running elevated PowerShell command: {}'.format(command_str))
            runAsAdmin(['powershell.exe', '-NoExit', '-Command', command_str])
    elif sys.argv[1] == "--install-sudo-command" and os.name == 'nt':
        # a single-user Python install already put its own Scripts dir on the user's PATH,
        # and that directory is writable without elevation -- prefer it over C:\Windows.
        install_dir = user_python_scripts_dir() or r'C:\Windows'
        whole_machine = (install_dir == r'C:\Windows')
        WINDOWS_PATH = os.path.join(install_dir, 'sudo.py')
        print('Installing "sudo" command into "{}"...'.format(install_dir))
        if not whole_machine or isUserAdmin():
            shutil.copy2(__file__, WINDOWS_PATH)
            shutil.copy2(os.path.dirname(os.path.abspath(__file__)) + r'\argv_quote.py',
                         os.path.join(install_dir, 'argv_quote.py'))
            shutil.copy2(os.path.dirname(os.path.abspath(__file__)) + r'\sudo_pause.bat',
                         os.path.join(install_dir, 'sudo_pause.bat'))
            shutil.copy2(os.path.dirname(os.path.abspath(__file__)) + r'\sudo_cd.bat',
                         os.path.join(install_dir, 'sudo_cd.bat'))
            # A generated sudo.bat, not "sudo" + PATHEXT's ".PY", is what actually gets
            # found and run -- ".bat" is already in the default PATHEXT, so this needs no
            # PATHEXT change at all, and completely sidesteps the ".py" file association
            # (which can be missing entirely on some Python installs, or get silently
            # overridden by Windows' own "Open With" / UserChoice picker even after we set
            # it correctly -- both seen in practice, both invisible to us to fix reliably).
            sudo_bat_path = os.path.join(install_dir, 'sudo.bat')
            with open(sudo_bat_path, 'w') as f:
                f.write('@echo off\r\n"{}" "{}" %*\r\n'.format(sys.executable, WINDOWS_PATH))
            print('Wrote "{}"'.format(sudo_bat_path))
            # An older version of this installer added ".PY" to PATHEXT, and (on a machine
            # that hit the now-fixed PATHEXT-repair bug) could leave it sorted AHEAD of
            # ".BAT" -- e.g. ".PY;.COM;.EXE;.BAT;...". Directory-first/extension-second
            # PATHEXT resolution means a leftover ".PY" ahead of ".BAT" makes bare "sudo"
            # still prefer the (association-dependent, possibly broken) sudo.py over the
            # sudo.bat above. Since sudo.bat needs no PATHEXT entry at all, clean up any
            # leftover ".PY" here -- a no-op if it was never added.
            set_env_variables_permanently_win({'PATHEXT': '-.PY'}, whole_machine=whole_machine)
            warn_if_native_sudo(install_dir)
            print()
            print('"sudo" is ready to use in any NEW cmd window -- no logoff needed for that.')
            print('(If a native sudo.exe was just moved on the system PATH above, log off and')
            print('back on for THAT specific change to reach every process.)')
            try:
                input('Hit <Enter> to continue . . .')
            except EOFError:
                pass
        else:
            runAsAdmin([os.path.abspath(__file__), '--install-sudo-command'], python_shell=True)
    elif any([arg.startswith(PREPEND_PATH_FLAG) for arg in sys.argv]) and os.name == 'nt':
        # internal: the elevated re-launch that warn_if_native_sudo() spawns to move an
        # install dir ahead of the native sudo.exe on the system PATH.
        flagged_arg = next(arg for arg in sys.argv if arg.startswith(PREPEND_PATH_FLAG))
        prepend_path_win(flagged_arg.split('=', 1)[1], whole_machine=True)
        try:
            input('Hit <Enter> to continue . . .')
        except EOFError:
            pass
    elif any([arg.startswith("--set-system-env") for arg in sys.argv]) and os.name == 'nt':
        if isUserAdmin():
            ctx = get_context("--set-system-env")
            set_env_variables_permanently_win(ctx, whole_machine=True)
            time.sleep(5)
        else:
            runAsAdmin([os.path.abspath(__file__)] + sys.argv[1:], None, python_shell=True)
    elif any([arg.startswith("--set-user-env") for arg in sys.argv]) and os.name == 'nt':
        ctx = get_context("--set-user-env")
        set_env_variables_permanently_win(ctx, whole_machine=False)
    else:  # normal operation
        if sys.argv[1] == 'ps' and os.name == 'nt':  # convenience alias for an elevated PowerShell
            sys.argv[1] = 'powershell'
        if sys.argv[1].startswith('salt-'):  # make "sudo salt-call" automatically pause
            sys.argv.insert(1, '--pause')

        if sys.argv[1] == '--pause':
            sys.argv[1] = 'sudo_pause.bat'
        else:
            sys.argv.insert(1, 'sudo_cd.bat')
        cwd = os.getcwd()
        sys.argv.insert(2, cwd)
        runAsAdmin(sys.argv[1:])


def install_entry_point():
    '''
    Target for the "windows-sudo-install" console script (see pyproject.toml). pip can
    install a small generated shim for this automatically, but -- unlike a classic
    setup.py install-time hook -- it can't run arbitrary code during "pip install"
    itself (that path only ever fires for a source/sdist build, not the prebuilt wheel
    "pip install windows-sudo" actually uses). So this is the one command a user runs
    once, by hand, after "pip install windows-sudo", equivalent to running
    "sudo.py --install-sudo-command" directly.
    :return:
    '''
    sys.argv = [sys.argv[0], '--install-sudo-command']
    main()


if __name__ == "__main__":
    main()
