import argparse
# Python built-in module for parsing command-line arguments.

def main():
    args = parse_args()
    args.func(args)
    
def parse_args():
    parser = argparse.ArgumentParser()
    # Create a new ArgumentParser object.
    
    commands = parser.add_subparsers(dest='command', required=True)
    # Add subparsers for different commands (like 'init', 'commit',...)
    # the 'dest' argument specifies the attribute name for the command.
    # and make the command argument required.
    
    commands.add_parser('init').set_defaults(func=init)
    
    return parser.parse_args()
    # This should return Namespace(command='init', func=<function 'init' below>) for 'ugit init'


def init(args):
    print("Initializing ugit repository...")