"""
Toy script for interactively testing "sudo".

Usage:
    sudo tests\\manual\\toy.py
"""
import ctypes
import os
import sys

elevated = bool(ctypes.windll.shell32.IsUserAnAdmin())

print('PID:', os.getpid())
print('cwd:', os.getcwd())
print('args:', sys.argv[1:])
print('Elevated:', elevated)
input('Press Enter to exit.')
