#!/usr/bin/env python3
# shebang: Allow the script to be run as an executable, using Python 3 as the interpreter (Unix-like systems).
# setup.py: Script to set up the ugit package.

from setuptools import setup
# setuptools: A Python package used for distributing Python packages.

setup (name = 'ugit', # Name for distribution.
       version = '1.0',
       packages = ['ugit'], # Code folders to include
       entry_points = {
           'console_scripts' : [
               'ugit = ugit.cli:main'
           ]
       })