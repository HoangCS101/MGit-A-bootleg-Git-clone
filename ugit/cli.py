# This file is in charge of parsing and processing user input

import argparse
# Python built-in module for parsing command-line arguments.
import os
import sys

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
    
    commands.add_parser('init').set_defaults(func=init)
    # 'ugit init' command
    
    hash_object_parser = commands.add_parser('hash-object')
    hash_object_parser.set_defaults(func=hash_object)
    hash_object_parser.add_argument('file')
    # 'ugit hash-object <file>' command
    
    cat_file_parser = commands.add_parser('cat-file')
    cat_file_parser.set_defaults(func=cat_file)
    cat_file_parser.add_argument('object')
    
    return parser.parse_args()
    # This should return Namespace(command='init', func=<function 'init' below>) for 'ugit init'


def init(args):
    data.init()
    print(f'Initialized ugit repository in {os.getcwd()}/{data.GIT_DIR}')
    
def hash_object(args):
    with open (args.file, 'rb') as f: # 'rb' for reading binary files
        print(data.hash_object(f.read()))
        
def cat_file(args):
    sys.stdout.flush()
    sys.stdout.buffer.write(data.get_object(args.object))
    
    # Here we use sys.stdout.buffer to write binary data directly to stdout.
    # Before that, we flush stdout to ensure that any buffered output is written immediately.
    # For example, if before this line there was a print statement, it would be flushed before writing the binary data.