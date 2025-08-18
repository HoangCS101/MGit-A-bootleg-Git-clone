# This file is in charge of parsing and processing user input

import argparse
# Python built-in module for parsing command-line arguments.
import os
import subprocess
import sys
import textwrap

from . import base
from . import data

def main():
    args = parse_args()
    # Parse the command-line arguments.
    # For example, if the user runs 
    #   'ugit hash-object example.txt'
    # parse_args should returns:
    #   Namespace(
    #       command='hash-object',
    #       file='example.txt',
    #       func=<function hash-object at 0x...>).
    
    args.func(args)
    # And this should be equivalent to calling:
    #   hash_object(args)
    
def parse_args():
    parser = argparse.ArgumentParser()
    # Create a new ArgumentParser object.
    
    commands = parser.add_subparsers(dest='command', required=True)
    # Add subparsers for different commands (like 'init', 'commit',...)
    # the 'dest' argument specifies the attribute name for the command.
    # and make the command argument required.
    
    oid = base.get_oid
    # basically an alias: assign the get_oid function from base module to 'oid'
    # so we can pass it to argparse's 'type' for input validation/conversion
    
    commands.add_parser('init').set_defaults(func=init)
    # 'ugit init' command
    
    hash_object_parser = commands.add_parser('hash-object')
    hash_object_parser.set_defaults(func=hash_object)
    hash_object_parser.add_argument('file')
    # 'ugit hash-object <file>' command
    
    cat_file_parser = commands.add_parser('cat-file')
    cat_file_parser.set_defaults(func=cat_file)
    cat_file_parser.add_argument('object', type=oid)
    
    write_tree_parser = commands.add_parser('write-tree')
    write_tree_parser.set_defaults(func=write_tree)
    
    read_tree_parser = commands.add_parser('read-tree')
    read_tree_parser.set_defaults(func=read_tree)
    read_tree_parser.add_argument('tree', type=oid)
    
    commit_parser = commands.add_parser('commit')
    commit_parser.set_defaults(func=commit)
    commit_parser.add_argument('-m', '--message', required=True)
    
    log_parser = commands.add_parser('log')
    log_parser.set_defaults(func=log)
    log_parser.add_argument('oid', default='@', type=oid, nargs='?')
    
    checkout_parser = commands.add_parser('checkout')
    checkout_parser.set_defaults(func=checkout)
    checkout_parser.add_argument('commit')
    
    tag_parser = commands.add_parser('tag')
    tag_parser.set_defaults(func=tag)
    tag_parser.add_argument('name')
    tag_parser.add_argument('oid', default='@', type=oid, nargs='?')
    
    k_parser = commands.add_parser('k')
    k_parser.set_defaults(func=k)
    # 'ugit k' command, similar to 'gitk', lists all refs
    
    branch_parser = commands.add_parser('branch')
    branch_parser.set_defaults(func=branch)
    branch_parser.add_argument('name', nargs='?')
    branch_parser.add_argument('start_point', default='@', type=oid, nargs='?')
    
    status_parser = commands.add_parser('status')
    status_parser.set_defaults(func=status)
    
    return parser.parse_args()
    # This should return Namespace(command='init', func=<function 'init' below>) for 'ugit init'


def init(args):
    base.init()
    print(f'Initialized ugit repository in {os.getcwd()}/{data.GIT_DIR}')
    
def hash_object(args):
    with open (args.file, 'rb') as f: # 'rb' for reading binary files
        print(data.hash_object(f.read()))
        
def cat_file(args):
    sys.stdout.flush()
    sys.stdout.buffer.write(data.get_object(args.object, expected='blob'))
    
    # Here we use sys.stdout.buffer to write binary data directly to stdout.
    # Before that, we flush stdout to ensure that any buffered output is written immediately.
    # For example, if before this line there was a print statement, it would be flushed before writing the binary data.

def write_tree(args):
    print(base.write_tree())
    
def read_tree(args):
    base.read_tree(args.tree)
    
def commit(args):
    print(base.commit(args.message))
    
def log(args):
    for oid in base.iter_commits_and_parents({args.oid}):
        # {args.oid} creates a set with a single element, args.oid
        # or else python would treat args.oid as a set of separated characters
        commit = base.get_commit(oid)
        print(f'commit {oid}\n')
        print(textwrap.indent(commit.message, '    '))
        print('')
        
        oid = commit.parent
        
def checkout(args):
    base.checkout(args.commit)

def tag(args):
    base.create_tag(args.name, args.oid)

def branch(args):
    if not args.name:
        current = base.get_branch_name()
        for branch in base.iter_branch_name():
            prefix = '*' if branch == current else ' '
            print(f'{prefix} {branch}')
    else:
        base.create_branch(args.name, args.start_point)
        print(f'Branch {args.name} created at {args.start_point[:10]}')
    
def k(args):
    dot = 'digraph commits {\n'
    
    oids = set()
    for refname, ref in data.iter_refs(deref=False):
        dot += f'"{refname}" [shape=note]\n'
        dot += f'"{refname}" -> "{ref.value}"\n'
        if not ref.symbolic:
            oids.add(ref.value)
    
    for oid in base.iter_commits_and_parents(oids):
        commit = base.get_commit(oid)
        dot += f'"{oid}" [shape=box style=filled lable="{oid[:10]}"]\n'
        if commit.parent:
            dot += f'"{oid}" -> "{commit.parent}"\n'
        
    dot += '}'
    print(dot)
    
    with subprocess.Popen(
            ['dot', '-Tx11', '/dev/stdin'], # '-Tgtk' is not supported anymore
            stdin=subprocess.PIPE) as proc:
        proc.communicate(input=dot.encode())
        
def status(args):
    HEAD = base.get_oid('@')
    branch = base.get_branch_name()
    if branch:
        print(f'On branch {branch}')
    else:
        print(f'HEAD deached at {HEAD[:10]}')
    