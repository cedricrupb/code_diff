from .isomap   import gumtree_isomap
from .editmap  import gumtree_editmap
from .chawathe import compute_chawathe_edit_script
from .ops      import (Update, Insert, Delete, Move)
from .ops      import EditScript
from .ops      import serialize_script, deserialize_script
from .ops      import json_serialize, json_deserialize

from .utils import NodeMapping

# Edit script ----------------------------------------------------------------

def compute_edit_script(source_ast, target_ast, min_height = 1, max_size = 1000, min_dice = 0.5, return_map = False):
    editmap = compute_edit_map(source_ast, target_ast, min_height=min_height, 
                                max_size=max_size, min_dice=min_dice)
    
    # If source_ast and target_ast only leaves
    if len(source_ast.children) == 0 and len(target_ast.children) == 0:
        editscript = EditScript([_update_leaf(source_ast, target_ast)])
    else:
        editscript = compute_chawathe_edit_script(editmap, source_ast, target_ast)

    if return_map:
        return EditScript(editscript), editmap
    
    return EditScript(editscript)


def compute_edit_map(source_ast, target_ast, min_height = 1, max_size = 1000, min_dice = 0.5):
    
    if len(source_ast.children) == 0 and len(target_ast.children) == 0:
        mapping = NodeMapping()
        mapping.add(source_ast, target_ast)
        return mapping

    isomap = compute_isomap(source_ast, target_ast, min_height=min_height)
    return gumtree_editmap(isomap, source_ast, target_ast, max_size, min_dice)


def compute_isomap(source_ast, target_ast, min_height = 1):
    isomap = gumtree_isomap(source_ast, target_ast, min_height)

    while len(isomap) == 0 and min_height > 0:
        min_height -= 1
        isomap = gumtree_isomap(source_ast, target_ast, min_height)
    
    return isomap

# Helper ---------------------------------------------------------------------

def _populate_isomap_recursively(isomap, source, target):
    
    queue = [(source, target)]
    while len(queue) > 0:
        source_node, target_node = queue.pop(0)

        assert len(source_node.children) == len(target_node.children), "An isomorph node should have same number of children"
        
        for i, source_child in enumerate(source_node.children):
            target_child = target_node.children[i]

            assert source_child.isomorph(target_child), f"Source child {source_child} is not isomorph to target child {target_child}"
            queue.append((source_child, target_child))
        
        isomap.add(source_node, target_node)


def diff_search_with_isomap(source_ast, target_ast):
    isomap = NodeMapping()

    if source_ast is None or source_ast.isomorph(target_ast): 
        _populate_isomap_recursively(isomap, source_ast, target_ast)
        return None, None, isomap

    queue = [(source_ast, target_ast)]
    while len(queue) > 0:
        source_node, target_node = queue.pop(0)

        if len(source_node.children) != len(target_node.children):
            return (source_node, target_node, isomap)
        
        next_children = []
        for i, source_child in enumerate(source_node.children):
            target_child = target_node.children[i]

            if source_child.isomorph(target_child):
                _populate_isomap_recursively(isomap, source_child, target_child)
            else:
                next_children.append((source_child, target_child))
        
        if len(next_children) == 1:
            queue.append(next_children[0])
        else:
            return (source_node, target_node, isomap)

    
# Update leaf ----------------------------------------------------------------

def _update_leaf(source_ast, target_ast):
    return Update(source_ast, target_ast.text)