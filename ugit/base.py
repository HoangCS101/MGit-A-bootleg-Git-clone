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
                
def is_ignored(path):
    return '.ugit' in path.split('/')