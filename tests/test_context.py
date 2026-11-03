"""
Round-trip tests for the --_context= argument that runAsAdmin passes to the
elevated copy of a program. These need no elevation, and run on any OS.
"""
import os
import shlex
import subprocess
import sys

import pytest

from windows_sudo import sudo

# the kind of context salt-bevy's bootstrap_bevy_member_here.py sends
CONTEXT = {
    'bevy': 'local',
    'interactive': True,
    'my_linux_user': 'vernon',
    'my_windows_password': '',
    'my_windows_user': 'None',
    'temp_settings_name': r'C:\Users\Owner\AppData\Local\Temp\salt-bevy_my_settings.conf',
    'user_name': 'vernon',
    'spaces and "quotes"': "it's here",
}


def test_encoder_writes_one_flow_style_line():
    ctx = sudo.encoder(CONTEXT)
    assert ctx.startswith('{') and ctx.endswith('}')
    assert '\n' not in ctx


def test_get_context_roundtrips_encoder_output(monkeypatch):
    monkeypatch.setattr(sys, 'argv', ['prog.py', 'local', sudo.ELEVATION_FLAG + '=' + sudo.encoder(CONTEXT)])
    assert sudo.get_context() == CONTEXT


def test_get_context_reads_block_style(monkeypatch):
    # what windows-sudo 2.1.1 and earlier sent: yaml.dump's default block style
    block = 'bevy: local\ninteractive: true\nmy_windows_user: None\n'
    monkeypatch.setattr(sys, 'argv', ['prog.py', sudo.ELEVATION_FLAG + '=' + block])
    assert sudo.get_context() == {'bevy': 'local', 'interactive': True, 'my_windows_user': 'None'}


def test_get_context_still_supplies_missing_braces(monkeypatch):
    # an unquoted value split by the shell, as described in get_context's docstring
    monkeypatch.setattr(sys, 'argv', ['prog.py', "--set-user-env='a':", "'b','c':'d'"])
    assert sudo.get_context('--set-user-env') == {'a': 'b', 'c': 'd'}


def test_get_context_bare_flag_returns_empty(monkeypatch):
    monkeypatch.setattr(sys, 'argv', ['prog.py', sudo.ELEVATION_FLAG])
    assert sudo.get_context() == {}


@pytest.mark.skipif(os.name != 'posix', reason='the sudo command line is built only on posix')
def test_context_survives_the_posix_sudo_command_line(monkeypatch):
    commands = []
    monkeypatch.setattr(subprocess, 'call', lambda cmd, shell: commands.append(cmd) or 0)
    sudo.runAsAdmin(['prog.py', 'local'], python_shell=True, context=CONTEXT)
    argv = shlex.split(commands[0])  # what the shell hands to sudo
    assert argv[:2] == ['sudo', sys.executable]
    monkeypatch.setattr(sys, 'argv', argv[2:])
    assert sudo.get_context() == CONTEXT
