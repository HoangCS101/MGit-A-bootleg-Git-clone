# codes for dealing with computing differences between trees

from collections import defaultdict

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
    
    output =''
    for path, o_from, o_to in compare_trees(t_from, t_to):
        if o_from != o_to:
            output += f'changed: {path}\n'
    return output
