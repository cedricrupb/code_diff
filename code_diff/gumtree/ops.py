import json
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



# Deserialize --------------------------------------------------------------------------------------------------------------------------------

class DASTNode:

    def __init__(self, type, position, text = None):
        self.type = type
        self.position = position
        self.text = text

    def __repr__(self):
        return "Node(%s, %s, %s)" % (self.type, str(self.text), self.position)


class InsertNode:

    def __init__(self, node_id, type, text = None):
        self.node_id = node_id
        self.type    = type
        self.text    = text

    def __repr__(self):
        return "%s(%s, %s)" % (self.node_id, self.type, str(self.text))


def _split_args(inst):
    args = []

    bracket_open = 0
    str_open     = False
    for i, c in enumerate(inst):

        # Lookahead
        if i > 0 and i < len(inst) - 1 and c in ["(", ")", ",", "\"", "\'"]:
            if inst[i - 1] == ":" and inst[i - 2] == c: continue
            if inst[i + 1] == ":" and inst[i + 2] == c: continue

        if c in ["\"", "\'"]:
            str_open = not str_open

        if str_open: continue

        if c == "(": 
            if bracket_open == 0: args.append(i)
            bracket_open += 1
            continue

        if c == ")": 
            bracket_open -= 1
            if bracket_open == 0: args.append(i)
            continue
            
        if bracket_open == 1 and c == ",":
            args.append(i)

    return [inst[args[i - 1] + 1: args[i]].strip() for i in range(1, len(args))]


def _deserialize_insert_node(node_registry, node_info):

    if "(" not in node_info or node_info in ["(:(", "):)"]:
        return InsertNode("T", *_parse_type(node_info))

    node_type, node_id = _split_args(node_info)

    if node_id in node_registry: return node_registry[node_id]

    insert_node = InsertNode(node_id, node_type)
    node_registry[node_id] = insert_node

    return insert_node


def _parse_type(node_type):
    if ":" in node_type:
        return node_type.split(":", 1)
    return node_type, None


def _deserialize_node(node_registry, node_info):
    
    if "(" in node_info:
        ast_type, ast_position = _split_args(node_info)
        ast_type, ast_text     = _parse_type(ast_type)
        return DASTNode(ast_type, ast_position, text = ast_text)
    
    if node_info in node_registry:
        return node_registry[node_info]

    return InsertNode(node_info, "unknown")


def _deserialize_update(node_registry, inst):
    target_node, update = _split_args(inst)
    target_node = _deserialize_node(node_registry, target_node)
    return Update(target_node, update)


def _deserialize_insert(node_registry, inst):
    new_node, target_node, position = _split_args(inst)

    new_node = _deserialize_insert_node(node_registry, new_node)
    target_node = _deserialize_node(node_registry, target_node)
    
    return Insert(target_node, new_node, int(position), -1)


def _deserialize_delete(node_registry, inst):
    target_node = _split_args(inst)[0]
    target_node = _deserialize_node(node_registry, target_node)
    return Delete(target_node)


def _deserialize_move(node_registry, inst):
    from_node, to_node, position = _split_args(inst)
    from_node = _deserialize_node(node_registry, from_node)
    to_node   = _deserialize_node(node_registry, to_node)
    return Move(to_node, from_node, int(position))
        

def deserialize_script(script_string):

    instructions = script_string.split("\n")[1:-1]

    script = []
    node_registry = {}
    for instruction in instructions:
        instruction = instruction.strip()

        if instruction.startswith("Update"):
            op = _deserialize_update(node_registry, instruction)
        if instruction.startswith("Insert"):
            op = _deserialize_insert(node_registry, instruction)
        if instruction.startswith("Delete"):
            op = _deserialize_delete(node_registry, instruction)
        if instruction.startswith("Move"):
            op = _deserialize_move(node_registry, instruction)

        script.append(op)

    return script


# Fast serialize -----------------------------------------------------------------------------------------------------------------------------

def _json_serialize_new_node(new_node_index, node):
    
    if node.node_id not in new_node_index:
        new_node_index[node.node_id] = len(new_node_index)

    return "N%d" % new_node_index[node.node_id]


def _json_serialize_ast_node(node):
   position  = node.position
   node_text = node.type

   if node.text: node_text += ":" + node.text

   return [node_text, position[0][0], position[0][1], position[1][0], position[1][1]]


def _json_serialize_node(new_node_index, node):
    
    if hasattr(node, 'node_id'):
        return _json_serialize_new_node(new_node_index, node)
    
    return _json_serialize_ast_node(node)


def json_serialize(edit_script):
    edit_ops = []
    new_node_index = {}

    for operation in edit_script:
        operation_name = operation.__class__.__name__
        target_node_str = _json_serialize_node(new_node_index, operation.target_node)

        if operation_name == "Update":
            edit_ops.append([operation_name, target_node_str, operation.value])
        
        elif operation_name == "Insert":
            
            new_node = operation.node

            if new_node[1] is None:
                new_node_index[operation.insert_id] = len(new_node_index)
                new_node_str = [new_node[0], "N%d" % new_node_index[operation.insert_id]]
            else: # Leaf node
                new_node_str = ["%s:%s" % new_node, "T"]

            edit_ops.append([operation_name, target_node_str, new_node_str])

        elif operation_name == "Move":

            new_node_str = _serialize_node(new_node_index, operation.node)

            edit_ops.append([operation_name, target_node_str, new_node_str, operation.position])

        elif operation_name == "Delete":
            edit_ops.append([operation_name, target_node_str])

    return json.dumps(edit_ops)


# Fast deserialize ----------------------------------------------------------------------