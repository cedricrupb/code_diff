from .isomap   import gumtree_isomap
from .editmap  import gumtree_editmap
from .chawathe import compute_chawathe_edit_script
from .ops      import (Update, Insert, Delete, Move)

# Edit script ----------------------------------------------------------------

def compute_edit_script(source_ast, target_ast, min_height = 1):

    # If source_ast and target_ast only leaves
    if len(source_ast.children) == 0 and len(target_ast.children) == 0:
        return [_update_leaf(source_ast, target_ast)]

    isomap = gumtree_isomap(source_ast, target_ast, min_height)

    while len(isomap) == 0 and min_height > 0:
        min_height -= 1
        isomap = gumtree_isomap(source_ast, target_ast, min_height)

    editmap = gumtree_editmap(isomap, source_ast, target_ast)
    editscript = compute_chawathe_edit_script(editmap, source_ast, target_ast)
    
    return editscript
    

# Update leaf ----------------------------------------------------------------

def _update_leaf(source_ast, target_ast):
    return Update(source_ast, target_ast.text)