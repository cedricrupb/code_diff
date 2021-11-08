from .isomap import gumtree_isomap

# Edit script ----------------------------------------------------------------

def compute_edit_script(source_ast, target_ast):
    
    isomap = gumtree_isomap(source_ast, target_ast)
    print(isomap)