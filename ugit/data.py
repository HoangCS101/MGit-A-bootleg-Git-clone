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
        
def update_ref(ref, oid):
    ref_path = os.path.join(GIT_DIR, ref)
    os.makedirs(os.path.dirname(ref_path), exist_ok=True)
    # exits_ok=True will not raise an error if the directory already exists
    with open(ref_path, 'w') as f:
        f.write(oid)
    
def get_ref(ref):
    ref_path = os.path.join(GIT_DIR, ref)
    if os.path.isfile(ref_path):
        # Check if the ref file exists first, we don't want to create a file if it doesn't exist
        with open(ref_path, 'r') as f:
            return f.read().strip() # strip to remove any trailing newline or spaces
        
def hash_object(data, type_='blob'): # data should be in bytes (e.g. b'hello world' -> binary)
    # type_ is the type of object, default is 'blob', the underscore is to avoid conflict or confusion with the built-in type
    # also to declare that it should be followed by a null byte
    obj = type_.encode() + b'\x00' + data
    # encode the type from string to bytes, add a null byte, and concatenate with data
    oid = hashlib.sha256(data).hexdigest() # dont forget to digest the sha256 HASH object
    with open(os.path.join(GIT_DIR, 'objects', oid), 'wb') as out: # 'wb' for binary write
        out.write(obj)
    return oid

def get_object(oid, expected='blob'):
    with open (os.path.join(GIT_DIR, 'objects', oid), 'rb') as f: # 'rb' for binary read
        obj = f.read()
    type_, _, content = obj.partition(b'\x00')
    # partition(<separator>) splits the bytes object into three parts: before the sep, the separator it self, and after the sep
    type_=type_.decode() # decode the type from bytes back to string
    
    # if expected != type_:
    #     raise ValueError(f"Expected object type '{expected}', but got '{type_}'")
    return content