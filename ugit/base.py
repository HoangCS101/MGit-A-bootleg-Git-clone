# For basic higher-level logic for ugit
# For example, using the object database implemented in data.py to implement higher-level structures for storing directories

import os

from . import data

def write_tree(directory='.'):
    entries = []
    with os.scandir(directory) as it:
        for entry in it:
            full = f'{directory}/{entry.name}'
            if is_ignored(full):
                continue
            if entry.is_file(follow_symlinks=False):
                # follow_symlinks=False -> do not follow symbolic links
                # for example, if the entry is a symlink to a file, we do not want to follow it
                # or, potentially, create a loop
                type_ = 'blob'
                with open(full, 'rb') as f:
                    oid = data.hash_object(f.read(), type_)
            elif entry.is_dir(follow_symlinks=False):
                type_ = 'tree'
                oid = write_tree(full) # Recursively call write_tree for subdirectories
            entries.append((entry.name, oid, type_))
            # Append the entry list with the (name, oid, type_) tuple
            
    tree=''.join(f'{type_} {oid} {name}\n' for name, oid, type_ in sorted(entries))
    # Sort entries by name and format them as 'type oid name\n'
    # to make sure that the tree is consistent and does not messed up the hash
    return data.hash_object(tree.encode(), type_='tree')
                
# _iter_tree_entries is a generator that will take an OID of a tree
# tokenize it line-by-line and yield the raw string values.
def _iter_tree_entries(oid):
    if not oid:
        return
    tree = data.get_object(oid,'tree')
    for entry in tree.decode().splitlines():
        type_, oid, name = entry.split(' ', 2)
        yield type_, oid, name
        
# get_tree uses _iter_tree_entries to recursively parse a tree into a dictionary.
def get_tree(oid,base_path=''):
    result = {}
    for type_, oid, name in _iter_tree_entries(oid):
        assert '/' not in name # not a path component
        assert name not in ('..','.') # no loops or security issues
        path = base_path + name
        if type_ == 'blob':
            result[path] = oid
        elif type_ == 'tree':
            result.update(get_tree(oid, base_path=path + '/'))
        else:
            assert False, f'Unknown type {type_} for {name}'
    return result
    # the result should look like:
    # {
    #   'file.txt': 'oid1',
    #   'dir/file2.txt': 'oid3',
    #   ...
    # }
    
def _empty_current_directory():
    for root, dirnames, filenames in os.walk('.', topdown = False):
        # os.walk returns a tuple (root, dirnames, filenames)
        # where root is the current directory,
        # dirnames is a list of directories in the current directory,
        # and filenames is a list of files in the current directory.
        # topdown=False is beneficial here since we want to delete files
        for filename in filenames:
            path = os.path.relpath(os.path.join(root, filename))
            if is_ignored(path) or not os.path.isfile(path): # double check needed for os.walk
                continue
            os.remove(path)
        for dirname in dirnames:
            path = os.path.relpath(os.path.join(root, dirname))
            if is_ignored(path) or not os.path.isdir(path):
                continue
            try:
                os.rmdir(path)
            except (FileNotFoundError, OSError):
                # Deletion might fail if the directory contains ignored files
                # so it's OK
                pass
            
# read_tree uses get_tree to get the file OIDs
# and writes them into the working directory.
def read_tree(tree_oid):
    _empty_current_directory()
    # Clear the current directory before writing the tree
    for path, oid in get_tree(tree_oid, base_path = './').items():
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open (path, 'wb') as f:
            f.write(data.get_object(oid))
        
def is_ignored(path):
    return '.ugit' in path.split('/')