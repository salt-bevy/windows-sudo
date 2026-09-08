"""
Go/no-go smoke tests for windows_sudo.sudo.

These only exercise code paths that need no elevation and touch no
persistent system state (no registry writes, no UAC prompts). They are
meant to catch import breakage and basic CLI regressions, not to be a
full behavioral test suite for the elevated operations themselves.
"""
import os
import subprocess
import sys

import pytest

from windows_sudo import sudo

pytestmark = pytest.mark.skipif(os.name != 'nt', reason='windows-sudo is Windows-only')


def run_sudo(*args):
    return subprocess.run(
        [sys.executable, sudo.__file__, *args],
        capture_output=True, text=True, timeout=15,
    )


def test_module_imports():
    assert sudo.__version__


@pytest.mark.parametrize('args', [(), ('--help',), ('-h',)])
def test_help_runs_without_elevation(args):
    result = run_sudo(*args)
    assert result.returncode == 0
    assert 'usage' in result.stdout.lower()


def test_version_runs_without_elevation():
    result = run_sudo('--version')
    assert result.returncode == 0
    assert sudo.__version__ in result.stdout


def test_has_context_false_by_default(monkeypatch):
    monkeypatch.setattr(sys, 'argv', ['sudo.py'])
    assert sudo.has_context() is False


def test_has_context_true_when_flag_present(monkeypatch):
    monkeypatch.setattr(sys, 'argv', ['sudo.py', sudo.ELEVATION_FLAG + '={}'])
    assert sudo.has_context() is True


def test_is_user_admin_short_circuits_on_context(monkeypatch):
    monkeypatch.setattr(sys, 'argv', ['sudo.py', sudo.ELEVATION_FLAG])
    assert sudo.isUserAdmin() is True


def test_is_user_admin_returns_bool_without_elevation(monkeypatch):
    monkeypatch.setattr(sys, 'argv', ['sudo.py'])
    assert isinstance(sudo.isUserAdmin(), bool)


def test_get_context_parses_from_argv(monkeypatch):
    monkeypatch.setattr(sys, 'argv', ['sudo.py', "--_context={'arg1': 'val1'}"])
    assert sudo.get_context() == {'arg1': 'val1'}


def test_get_context_missing_flag_returns_empty(monkeypatch):
    monkeypatch.setattr(sys, 'argv', ['sudo.py', 'some-command'])
    assert sudo.get_context() == {}


def test_native_sudo_path_is_under_system32():
    path = sudo.native_sudo_path()
    assert path.lower().endswith(r'system32\sudo.exe')


def test_native_sudo_present_returns_bool():
    assert isinstance(sudo.native_sudo_present(), bool)


def test_user_python_scripts_dir_returns_str_or_none():
    result = sudo.user_python_scripts_dir()
    assert result is None or (isinstance(result, str) and os.path.isdir(result))


@pytest.mark.parametrize('args, expected', [
    (('plain',), 'plain'),
    (('has space',), '"has space"'),
])
def test_quote_roundtrips_simple_args(args, expected):
    from windows_sudo.argv_quote import quote
    assert quote(*args) == expected


def test_salt_flag_expands_to_salt_call_local_and_pauses(monkeypatch):
    calls = []
    monkeypatch.setattr(sudo, 'runAsAdmin', lambda cmdLine=None, **kw: calls.append(cmdLine))
    monkeypatch.setattr(os, 'getcwd', lambda: r'C:\somewhere')
    monkeypatch.setattr(sys, 'argv', ['sudo.py', '--salt', 'some', 'commands'])
    sudo.main()
    assert calls == [['sudo_pause.bat', r'C:\somewhere', 'salt-call', '--local', 'some', 'commands']]
