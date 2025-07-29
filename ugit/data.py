# This file manages the data in .ugit directory. here will be the code that actually touches files on disk.add()

import os

GIT_DIR = '.ugit'

def init():
    if not os.path.exists(GIT_DIR): # Check directory existence in cwd
        os.makedirs(GIT_DIR)
        print(f"Created directory: {GIT_DIR}")
    else:
        print(f"Directory {GIT_DIR} already exists.")