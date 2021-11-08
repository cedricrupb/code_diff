from .isomap  import gumtree_isomap
from .editmap import gumtree_editmap

# Edit script ----------------------------------------------------------------

def compute_edit_script(source_ast, target_ast):
    
    isomap = gumtree_isomap(source_ast, target_ast)
    print(isomap)
    print("----------------------------------------------------------------")

    editmap = gumtree_editmap(isomap, source_ast, target_ast)

    print(editmap)
    