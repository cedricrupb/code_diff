from dataclasses import dataclass
from typing import Any, Tuple

@dataclass
class EditOperation:
    target_node: Any

@dataclass
class Update(EditOperation):
    value: Any

@dataclass
class Insert(EditOperation):
    node: Tuple[str, Any]
    position: int
    insert_id: int # This is necessary to keep track of nodes (TODO: Better solution?)

@dataclass
class Move(EditOperation):
    node: Any
    position: int

@dataclass
class Delete(EditOperation):
    pass


# Serialization --------------------------------

import json


def _serialize_new_node(new_node_index, node):
    
    if node.node_id not in new_node_index:
        new_node_index[node.node_id] = len(new_node_index)

    return "N%d" % new_node_index[node.node_id]

def _serialize_ast_node(node):
   position  = node.position
   node_text = node.type

   if node.text: node_text += ":" + node.text
   
   return "(%s, line %d:%d - %d:%d)" % (node_text, position[0][0], position[0][1], position[1][0], position[1][1]) 


def _serialize_node(new_node_index, node):
    
    if hasattr(node, 'node_id'):
        return _serialize_new_node(new_node_index, node)
    
    return _serialize_ast_node(node)


def serialize_script(edit_script, indent = 0):
    
    sedit_script = []
    new_node_index = {}

    for operation in edit_script:

        operation_name = operation.__class__.__name__
        target_node_str = _serialize_node(new_node_index, operation.target_node)

        if operation_name == "Update":
            sedit_script.append("%s(%s, %s)" % (operation_name, target_node_str, operation.value))
        
        elif operation_name == "Insert":
            
            new_node = operation.node

            if new_node[1] is None:
                new_node_index[operation.insert_id] = len(new_node_index)
                new_node_str = "(%s, %s)" % (new_node[0], "N%d" % new_node_index[operation.insert_id])
            else: # Leaf node
                new_node_str = "%s:%s" % new_node

            sedit_script.append("%s(%s, %s, %d)" % (operation_name, new_node_str, target_node_str, operation.position))

        elif operation_name == "Move":

            new_node_str = _serialize_node(new_node_index, operation.node)

            sedit_script.append("%s(%s, %s, %d)" % (operation_name, new_node_str, target_node_str, operation.position))

        elif operation_name == "Delete":
            sedit_script.append("%s(%s)" % (operation_name, target_node_str))

    if indent > 0:
        sedit_script = [" "*indent + e for e in sedit_script]
        return "[\n%s\n]" % (",\n").join(sedit_script)

    return "[%s]" % ", ".join(sedit_script)
