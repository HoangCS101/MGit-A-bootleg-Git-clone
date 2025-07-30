# This file manages the data in .ugit directory. here will be the code that actually touches files on disk.add()

import hashlib
import os

GIT_DIR = '.ugit'

def init():
    if not os.path.exists(GIT_DIR): # Check directory existence in cwd
        os.makedirs(GIT_DIR)
        os.makedirs(os.path.join(GIT_DIR, 'objects'))
        print(f"Created directory: {GIT_DIR}")
    else:
        print(f"Directory {GIT_DIR} already exists.")
        
def hash_object(data): # data should be in bytes (e.g. b'hello world' -> binary)
    oid = hashlib.sha256(data).hexdigest() # dont forget to digest the sha256 HASH object
    with open(os.path.join(GIT_DIR, 'objects', oid), 'wb') as out: # 'wb' for binary write
        out.write(data)
    return oid

def get_object(oid):
    with open (os.path.join(GIT_DIR, 'objects', oid), 'rb') as f: # 'rb' for binary read
        return f.read()