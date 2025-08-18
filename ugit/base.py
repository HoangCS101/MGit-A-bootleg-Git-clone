# For basic higher-level logic for ugit
# For example, using the object database implemented in data.py to implement higher-level structures for storing directories

import itertools
import operator
import os
import string

from collections import deque, namedtuple

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
        
def commit(message):
    commit = f'tree {write_tree()}\n'
    
    HEAD = data.get_ref('HEAD').value
    if HEAD:
        commit += f'parent {HEAD}\n'
    
    commit += '\n'
    commit += f'{message}\n'
    
    oid = data.hash_object(commit.encode(), type_='commit')
    data.update_ref('HEAD', data.RefValue(symbolic=False,value=oid))
    return oid

# call read_tree and set HEAD to the commit OID
def checkout (name): # name could be and OID or a branch name
    oid = get_oid(name)
    commit = get_commit(oid)
    read_tree(commit.tree)
    
    if is_branch(name):
        HEAD = data.RefValue(symbolic=True, value=f'refs/heads/{name}')
    else:
        HEAD = data.RefValue(symbolic=False, value=oid)
        
    data.update_ref('HEAD', HEAD, deref=False)

def create_tag(name, oid):
    data.update_ref(os.path.join('refs', 'tags', name), data.RefValue(symbolic=False,value=oid))

def create_branch(name, oid):
    data.update_ref(os.path.join('refs', 'heads', name), data.RefValue(symbolic=False,value=oid))

Commit = namedtuple('Commit', ['tree', 'parent', 'message'])

def is_branch(branch):
    return data.get_ref(f'refs/heads/{branch}').value is not None

def get_commit(oid):
    parent = None
    
    commit = data.get_object(oid, expected='commit').decode()
    lines = iter(commit.splitlines())
    for line in itertools.takewhile(operator.truth, lines):
        # takewhile will stop when encountering an empty line
        key, value = line.split(' ', 1)
        if key == 'tree':
            tree = value
        elif key == 'parent':
            parent = value
        else:
            assert False, f'Unknown field {key} in commit {oid}'
    
    message = '\n'.join(lines)
    # since the first 3 lines are iterated, the remaining line is the message
    return Commit(tree=tree, parent=parent, message=message)

def iter_commits_and_parents(oids):
    oids = deque(oids)
    visited = set()
    # use deque to preserve order and allow fast appends and pops from both ends
    # while visited set() ensures the contain unique values
    
    while oids:
        oid = oids.popleft()
        if not oid or oid in visited:
            continue
        visited.add(oid)
        yield oid
        
        commit = get_commit(oid)
        oids.appendleft(commit.parent)

def get_oid(name):
    if name =='@': name =  'HEAD'
    
    # name is ref
    refs_to_try = [
        f'{name}', # for name='refs/tags/tag_name'
        f'refs/{name}', # for name='tags/tag_name'
        f'refs/tags/{name}', # for name='tag_name'
        f'refs/heads/{name}', # needed for future change
    ]
    for ref in refs_to_try:
        if data.get_ref(ref, deref=False).value:
            return data.get_ref(ref).value
    
    # name is SHA256 (OID)
    is_hex = all(c in string.hexdigits for c in name) and len(name) == 64
    # 256 bits = 32 bytes = 64 hex digits (2 hex digits per byte)
    if is_hex:
        return name
    
    assert False, f'Unknown name {name}'
    
def is_ignored(path):
    return '.ugit' in path.split('/')