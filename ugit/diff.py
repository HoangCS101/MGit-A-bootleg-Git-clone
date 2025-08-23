# codes for dealing with computing differences between trees

import subprocess
# to spawn new processes, connect to their input/output/error pipes, and obtain their return codes

from collections import defaultdict
from tempfile import NamedTemporaryFile as Temp
# for creating named temporary file, which can be accessed via real file's name


from . import data

def compare_trees(*trees): # allow n tree (diff_trees passes 2)
    entries = defaultdict(lambda: [None] * len(trees))
    # -> for each new key -> [None, None] (2 trees)
    
    # Lets say we have these trees:
    # t_from = {
    #     "a.txt": "hash123",
    #     "b.txt": "hash456",
    # }
    # t_to = {
    #     "a.txt": "hash123",   # unchanged
    #     "b.txt": "hash789",   # changed
    #     "c.txt": "hash000",   # added
    # }
    for i, tree in enumerate(trees):
        for path, oid in tree.items():
            entries[path][i] = oid
    # Then with each loop:
    # 1st:
    # {
    #     "a.txt": ["hash123", None],
    #     "b.txt": ["hash456", None],
    # }
    # 2nd:
    # {
    #     "a.txt": ["hash123", "hash123"],
    #     "b.txt": ["hash456", "hash789"],
    #     "c.txt": [None, "hash000"]
    # }

            
    for path, oids in entries.items():
        yield(path, *oids)
        # and finally returns:
        # ("a.txt", "hash123", "hash123")
        # ("b.txt", "hash456", "hash789")
        # ("c.txt", None, "hash000")

        
def diff_trees(t_from, t_to): # prev tree vs next tree
    # each of them are in the format of
    # {
    #   'file.txt': 'oid1',
    #   'dir/file2.txt': 'oid3',
    #   ...
    # }
    # from base.get_tree()
    
    output = b''
    for path, o_from, o_to in compare_trees(t_from, t_to):
        if o_from != o_to:
            output += diff_blobs(o_from, o_to, path)
    return output

def diff_blobs(o_from, o_to, path='blob'):
    with Temp() as f_from, Temp() as f_to:
    # create 2 temp files as 'f_from' and 'f_to', existing only within 'with'
    # temp files are needed since raw binary files in .ugit/objects cant be compared by 'diff'
        for oid, f in ((o_from, f_from), (o_to, f_to)):
            if oid:
                f.write(data.get_object(oid))
                f.flush()
                # normally python will automatically flush the buffer when:
                # closed() -> close file
                # out of 'with'
                # buffer overflow
                # here files content is needed within another process
                # which is calling 'diff' using 'subprocess'
                
        with subprocess.Popen( # Process open
            ['diff', '--unified', '--show-c-function',
             '--label', f'a/{path}', f_from.name,
             '--label', f'b/{path}', f_to.name],
            stdout=subprocess.PIPE) as proc:
            # stdout=subprocess.PIPE request result to be piped into python (not printed to terminal)
            # 'with ... as proc': context manager is used to make sure 'proc' is release when out of 'with'
            output, _ = proc.communicate()
            # interact with process, here send no stdin (input)
            # read data from stdout (output) and stderr (ignored)
            # until end-of-file is reached. Wait for process to terminate.

        return output
