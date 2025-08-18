# This file manages the data in .ugit directory. here will be the code that actually touches files on disk.add()

import hashlib
import os

from collections import namedtuple

GIT_DIR = '.ugit'

def init():
    if not os.path.exists(GIT_DIR): # Check directory existence in cwd
        os.makedirs(GIT_DIR)
        os.makedirs(os.path.join(GIT_DIR, 'objects'))
        print(f"Created directory: {GIT_DIR}")
    else:
        print(f"Directory {GIT_DIR} already exists.")
        
RefValue = namedtuple('RefValue', ['symbolic','value'])
        
def update_ref(ref, value, deref=True):
    ref = _get_ref_internal(ref, deref)[0]
    
    assert value.value
    if value.symbolic:
        value = f'ref: {value.value}'
    else:
        value = value.value
    
    ref_path = os.path.join(GIT_DIR, ref)
    os.makedirs(os.path.dirname(ref_path), exist_ok=True)
    # exits_ok=True will not raise an error if the directory already exists
    with open(ref_path, 'w') as f:
        f.write(value)
    
def get_ref(ref, deref=True): # ref here is expected to be a relative path from GIT_DIR
    return _get_ref_internal(ref, deref)[1]
    
# _get_ref_internal returns the path and the value of the last ref pointed by a symbolic ref
# Means:
# non-symbolic ref -> return the ref name and value
# symbolic ref -> dereference recursively and return the last non-symbolic ref
def _get_ref_internal(ref, deref):    
    ref_path = os.path.join(GIT_DIR, ref)
    value = None
    if os.path.isfile(ref_path):
        # Check if the ref file exists first, we don't want to create a file if it doesn't exist
        with open(ref_path, 'r') as f:
            value = f.read().strip() # strip to remove any trailing newline or spaces
    
    symbolic = bool(value) and value.startswith('ref:')
    if symbolic:
        value = value.split(':',1)[1].strip()
        # ref:<refname> -> split by ':' (1 time only), take the second part
        if deref:
            return _get_ref_internal(value, deref=True)
    
    return ref, RefValue(symbolic=symbolic, value=value)
    
def iter_refs(prefix='', deref=True):
    refs = ['HEAD']
    for root, _, filenames in os.walk(os.path.join(GIT_DIR, 'refs')):
        # root = '.../.ugit/refs/tags' (second level)
        # for example, if the file structure is:
        # .../.ugit/
        #       refs/
        #          tags/
        #           fileA
        #           fileB
        # then os.walk will yield:
        # first level: root = '.../.ugit/refs', dirnames = ['tags'], filenames = []
        # second level: root = '.../.ugit/refs/tags', dirnames = [], filenames = ['fileA', 'fileB']
        
        root = os.path.relpath(root, GIT_DIR)
        # from GIT_DIR = '.../.ugit' to root, relpath returns 'refs/tags'
        
        refs.extend(os.path.join(root, f) for f in filenames)
        # += 'refs/tags/filename' for each file in the 'refs/tags' directory
        
    for refname in refs:
        if not refname.startswith(prefix):
            continue
        yield refname, get_ref(refname, deref=deref)
        
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