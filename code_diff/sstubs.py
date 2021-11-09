from enum import Enum
import re

class SStubPattern(Enum):

    MULTI_STMT                     = 0
    SINGLE_STMT                    = 1
    SINGLE_TOKEN                   = 2
    NO_STMT                        = 3

    # Functions
    WRONG_FUNCTION_NAME            = 4

    SAME_FUNCTION_MORE_ARGS        = 5
    SAME_FUNCTION_LESS_ARGS        = 6
    SAME_FUNCTION_WRONG_CALLER     = 7
    SAME_FUNCTION_SWAP_ARGS        = 8

    ADD_FUNCTION_AROUND_EXPRESSION = 9
    ADD_METHOD_CALL                = 10

    # Changes (single token)
    CHANGE_IDENTIFIER_USED         = 11
    CHANGE_NUMERIC_LITERAL         = 12
    CHANGE_BOOLEAN_LITERAL         = 13

    # Change operator / operand
    CHANGE_UNARY_OPERATOR          = 14
    CHANGE_BINARY_OPERATOR         = 15 
    CHANGE_BINARY_OPERAND          = 16

    # Changes (Access)
    CHANGE_ATTRIBUTE_USED          = 17
    CHANGE_KEYWORD_ARGUMENT_USED   = 18
    CHANGE_CONSTANT_TYPE           = 19

    ADD_ELEMENTS_TO_ITERABLE       = 20
    ADD_ATTRIBUTE_ACCESS           = 21 

    # If condition
    MORE_SPECIFIC_IF               = 21
    LESS_SPECIFIC_IF               = 22


# SStub classification -------------------------------

def classify_sstub(source_ast, target_ast):
    # Assume tree is minimized to smallest edit

    if len(source_ast.children) == 0 and len(target_ast.children) == 0:
        return single_token_edit(source_ast, target_ast)

    if source_ast.parent.type == "call" and target_ast.parent.type == "call":
        source_name = source_ast.parent.children[0]
        target_name = target_ast.parent.children[0]

        if source_name.text == target_name.text:
            return same_function_mod(source_ast, target_ast)

    if _query_path(source_ast, "if_statement", "condition"):
        return change_if_statement(source_ast, target_ast)

    if source_ast.type in ["tuple", "list", "dictionary", "set"]:
        return change_iterable(source_ast, target_ast)

    if target_ast.type == "call":
        return add_function(source_ast, target_ast)

    if target_ast.type == "attribute":
        return add_attribute_access(source_ast, target_ast)

    return SStubPattern.SINGLE_STMT
    



# Single token edits --------------------------------

def _query_path(ast_node, type_query, edge_query = "*", depth = 1e9):

    last    = None
    current = ast_node
    while current is not None:

        if current.type == type_query:
            
            if edge_query == "*":
                return True
            else:
                if hasattr(current, "backend"):
                    edge_child = current.backend.child_by_field_name(edge_query)
                    return edge_child == last.backend

        last    = current
        current = current.parent
        depth  -= 1
        if depth < 0: break
    
    return False


def wrong_function_name(source_ast, target_ast):
    return _query_path(source_ast, "call", "function")


def change_numeric_literal(source_ast, target_ast):
    return source_ast.type in ["integer", "float"] and target_ast.type in ["integer", "float"]


def change_boolean_literal(source_ast, target_ast):
    return source_ast.type in ["false", "true"] and target_ast.type in ["false", "true"]


def change_attribute_used(source_ast, target_ast):
    if source_ast.type == "identifier":
        return _query_path(source_ast, "attribute", "attribute", depth = 1)
    return False


def change_identifier_used(source_ast, target_ast):
    return source_ast.type == "identifier"


def change_binary_operator(source_ast, target_ast):
    if _query_path(source_ast, "binary_operator", "*", depth = 1):
        return (not _query_path(source_ast, "binary_operator", "left", depth = 1) 
                    and not _query_path(source_ast, "binary_operator", "right", depth = 1))
    return False


def _to_plain_constant(text):
    
    if "\'" in text: text = text[1:-1]
    if "\"" in text: text = text[1:-1]

    try:
        return float(text)
    except:
        try:
            return float(int(text))
        except:
            return text


def change_constant_type(source_ast, target_ast):
    
    if source_ast.type == "identifier": return False
    if target_ast.type == "identifier": return False

    if source_ast.type == target_ast.type: return False

    source_text = _to_plain_constant(source_ast.text)
    target_text = _to_plain_constant(target_ast.text)

    return source_text == target_text


def change_keyword_argument_used(source_ast, target_ast):
    if source_ast.type == "identifier":
        return _query_path(source_ast, "keyword_argument", "name", depth = 1)
    return False


def same_function_wrong_caller(source_ast, target_ast):
    if not source_ast.type == "identifier": return False

    if not _query_path(source_ast, "call", "function", depth = 2): return False

    return _query_path(source_ast, "attribute", "object", depth = 1)



single_token_edits = {
    SStubPattern.WRONG_FUNCTION_NAME: wrong_function_name,
    SStubPattern.CHANGE_CONSTANT_TYPE: change_constant_type,
    SStubPattern.CHANGE_NUMERIC_LITERAL: change_numeric_literal,
    SStubPattern.CHANGE_BOOLEAN_LITERAL: change_boolean_literal,
    SStubPattern.CHANGE_ATTRIBUTE_USED: change_attribute_used,
    SStubPattern.CHANGE_KEYWORD_ARGUMENT_USED : change_keyword_argument_used,
    SStubPattern.SAME_FUNCTION_WRONG_CALLER: same_function_wrong_caller,
    SStubPattern.CHANGE_IDENTIFIER_USED: change_identifier_used,
    SStubPattern.CHANGE_BINARY_OPERATOR: change_binary_operator,
}


def single_token_edit(source_ast, target_ast):
    
    for key, test_fn in single_token_edits.items():
        if test_fn(source_ast, target_ast):
            return key
        
    return SStubPattern.SINGLE_TOKEN


# Same function --------------------------------


def same_function_more_args(source_ast, target_ast):
    
    if len(source_ast.children) >= len(target_ast.children):
        return False

    arguments = source_ast.children
    for arg in arguments:
        if not any(t.isomorph(arg) for t in target_ast.children):
            return False
        
    return True


def same_function_less_args(source_ast, target_ast):
    
    if len(source_ast.children) <= len(target_ast.children):
        return False

    arguments = target_ast.children
    for arg in arguments:
        if not any(t.isomorph(arg) for t in source_ast.children):
            return False
        
    return True


def same_function_swap_args(source_ast, target_ast):

    if len(source_ast.children) != len(target_ast.children):
        return False

    arguments = source_ast.children
    for arg in arguments:
        if not any(t.isomorph(arg) for t in target_ast.children):
            return False

    return True


same_function_edits = {
    SStubPattern.SAME_FUNCTION_MORE_ARGS: same_function_more_args,
    SStubPattern.SAME_FUNCTION_LESS_ARGS: same_function_less_args,
    SStubPattern.SAME_FUNCTION_SWAP_ARGS: same_function_swap_args,
}


def same_function_mod(source_ast, target_ast):
    
    if source_ast.type != "argument_list" or target_ast.type != "argument_list":
        return SStubPattern.SINGLE_STMT

    for key, test_fn in same_function_edits.items():
        if test_fn(source_ast, target_ast):
            return key
        
    return SStubPattern.SINGLE_STMT


# If statement ----------------------------------------------------------------


def more_specific_if(source_ast, target_ast):
    return any(c.isomorph(source_ast) for c in target_ast.children)


def less_specific_if(source_ast, target_ast):
    return any(c.isomorph(target_ast) for c in source_ast.children)


def change_if_statement(source_ast, target_ast):
    
    if more_specific_if(source_ast, target_ast):
        return SStubPattern.MORE_SPECIFIC_IF

    if less_specific_if(source_ast, target_ast):
        return SStubPattern.LESS_SPECIFIC_IF

    return SStubPattern.SINGLE_STMT

# Change iterable ----------------------------------------------------------------

def add_elements_to_iterable(source_ast, target_ast):
    
    if len(source_ast.children) >= len(target_ast.children):
        return False

    for c in source_ast.children:
        if not any(t.isomorph(c) for t in target_ast.children):
            return False
        
    return True


def change_iterable(source_ast, target_ast):
    
    if add_elements_to_iterable(source_ast, target_ast):
        return SStubPattern.ADD_ELEMENTS_TO_ITERABLE

    return SStubPattern.SINGLE_STMT


# ADD CALL AROUND STATEMENT ----------------------------------------------------------------

def add_function_around_expression(source_ast, target_ast):
    argument_list = target_ast.children[-1]
    assert argument_list.type == "argument_list", str(argument_list)

    if len(argument_list.children) != 3: return False

    for arg in argument_list.children:
        if arg.isomorph(source_ast):
            return True

    return False


def add_function(source_ast, target_ast):

    if add_function_around_expression(source_ast, target_ast):
        return SStubPattern.ADD_FUNCTION_AROUND_EXPRESSION

    if add_method_call(source_ast, target_ast):
        return SStubPattern.ADD_METHOD_CALL

    return SStubPattern.SINGLE_STMT


# ADD METHOD ----------------------------------------------------------------

def add_method_call(source_ast, target_ast):
    
    attribute = target_ast.children[0]

    if attribute.type != "attribute": return False

    return attribute.children[0].isomorph(source_ast)

# ADD attribute -------------------------------------------------------------


def add_attribute_access(source_ast, target_ast):
    if target_ast.children[0].isomorph(source_ast):
        return SStubPattern.ADD_ATTRIBUTE_ACCESS
    
    return SStubPattern.SINGLE_STMT

    