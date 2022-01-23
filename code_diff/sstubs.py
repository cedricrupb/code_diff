from enum import Enum

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
    MORE_SPECIFIC_IF               = 22
    LESS_SPECIFIC_IF               = 23

    # STRING
    CHANGE_STRING_LITERAL          = 24 # This is not a sstub pattern but helpful for scanning results


# SStub classification -------------------------------

def classify_sstub(source_ast, target_ast):
    # Assume tree is minimized to smallest edit

    classifier_fns = []

    if len(source_ast.children) == 0 and len(target_ast.children) == 0:
        classifier_fns.append(single_token_edit)

    if source_ast.parent.type == "call" and target_ast.parent.type == "call":
        source_name = _call_name(source_ast.parent)
        target_name = _call_name(target_ast.parent)

        if source_name == target_name:
            classifier_fns.append(same_function_mod)

    if (_query_path(source_ast, "if_statement", "condition")
         or _query_path(source_ast, "elif_clause", "condition")
         or _query_path(source_ast, "while_statement", "condition")):
        classifier_fns.append(change_if_statement)

    if source_ast.type in ["tuple", "list", "dictionary", "set"]:
        classifier_fns.append(change_iterable)

    if target_ast.type == "call" or target_ast.parent.type == "call":
        classifier_fns.append(add_function)

    if target_ast.type == "attribute":
        classifier_fns.append(add_attribute_access)

    if "operator" in source_ast.type or "operator" in target_ast.type:
        if is_unary_operator_change(source_ast, target_ast):
            return SStubPattern.CHANGE_UNARY_OPERATOR

    # Now run all classifier functions
    for classifier_fn in classifier_fns:
        result = classifier_fn(source_ast, target_ast)

        if result != SStubPattern.SINGLE_STMT:
            return result

    if is_binary_operand(source_ast, target_ast):
        return SStubPattern.CHANGE_BINARY_OPERAND

    return SStubPattern.SINGLE_STMT


# Utils -------------------------------------------------------------------------

def _call_name(ast_node):
    function_node = ast_node.children[0]

    right_most = function_node
    while len(right_most.children) > 0:
        right_most = right_most.children[-1]
    
    return right_most.text



def pisomorph(A, B):
    if A.isomorph(B): return True

    if A.type == "parenthesized_expression":
        return pisomorph(A.children[1], B)
    
    if B.type == "parenthesized_expression":
        return pisomorph(A, B.children[1])
    
    return False

    

# Binary operand ----------------------------------------------------------------


def is_binary_operand(source_ast, target_ast):

    for bin_op_type in ["binary_operator", "comparison_operator", "boolean_operator"]:
        for direction in ["left", "right"]:
            if (_query_path(source_ast, bin_op_type, direction, depth = 1)):
                return True
    
    return False



# Single token edits --------------------------------

def _query_path(ast_node, type_query, edge_query = "*", depth = 1e9):

    last    = None
    current = ast_node
    while current is not None:

        if current.type == type_query:
            
            if edge_query == "*":
                return True
            elif last is not None:
                if hasattr(current, "backend"):
                    edge_child = current.backend.child_by_field_name(edge_query)
                    return edge_child == last.backend

        last    = current
        current = current.parent
        depth  -= 1
        if depth < 0: break
    
    return False



def _get_parent(ast_node, type_query, edge_query = "*", depth = 1e9):

    last    = None
    current = ast_node
    while current is not None:

        if current.type == type_query:
            
            if edge_query == "*":
                return current
            elif last is not None:
                if hasattr(current, "backend"):
                    edge_child = current.backend.child_by_field_name(edge_query)
                    if edge_child == last.backend:
                        return current

        last    = current
        current = current.parent
        depth  -= 1
        if depth < 0: break
    
    return None



def wrong_function_name(source_ast, target_ast):
    if not source_ast.type == "identifier": return False
    if not target_ast.type == "identifier": return False

    func_call = _get_parent(source_ast, "call", "function")
    if func_call is None: return False
    
    right_most = func_call.backend.child_by_field_name("function")
    while right_most is not None and right_most != source_ast.backend:
        if len(right_most.children) > 0:
            right_most = right_most.children[-1]
        else:
            right_most = None

    return right_most is not None


def change_numeric_literal(source_ast, target_ast):
    return source_ast.type in ["integer", "float"] and target_ast.type in ["integer", "float"]


def change_string_literal(source_ast, target_ast):
    return source_ast.type == "string" and target_ast.type == "string"


def change_boolean_literal(source_ast, target_ast):
    return source_ast.type in ["false", "true"] and target_ast.type in ["false", "true"]


def change_attribute_used(source_ast, target_ast):
    if source_ast.type == "identifier":
        return _query_path(source_ast, "attribute", "attribute", depth = 1)
    return False


def change_identifier_used(source_ast, target_ast):

    # Following ManySStuBs we ignore the following Method declaration, Class Declaration, Variable Declaration
    if any(x in source_ast.parent.type for x in ["definition", "declaration"]):
        return False

    return source_ast.type == "identifier" and target_ast.type == "identifier"


def change_binary_operator(source_ast, target_ast):

    if source_ast.parent.type in ["binary_operator", "boolean_operator", "comparison_operator"]:
        bin_op = source_ast.parent
        return bin_op.children[1] == source_ast

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
    SStubPattern.CHANGE_BINARY_OPERATOR: change_binary_operator,
    SStubPattern.CHANGE_BINARY_OPERAND:  is_binary_operand,
    SStubPattern.CHANGE_IDENTIFIER_USED: change_identifier_used,
    SStubPattern.CHANGE_STRING_LITERAL: change_string_literal,
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
        if not any(pisomorph(t, arg) for t in target_ast.children):
            return False
        
    return True


def same_function_less_args(source_ast, target_ast):
    
    if len(source_ast.children) <= len(target_ast.children):
        return False

    arguments = target_ast.children
    for arg in arguments:
        if not any(pisomorph(t, arg) for t in source_ast.children):
            return False
        
    return True


def same_function_swap_args(source_ast, target_ast):

    if len(source_ast.children) != len(target_ast.children):
        return False

    src_arguments    = source_ast.children
    target_arguments = target_ast.children

    diff_args = [i for i, src_arg in enumerate(src_arguments) if not pisomorph(src_arg, target_arguments[i])]

    if len(diff_args) != 2: return False

    swap_0, swap_1 = diff_args
    return (pisomorph(src_arguments[swap_0], target_arguments[swap_1])
             and pisomorph(src_arguments[swap_1], target_arguments[swap_0]))


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
    
    if not target_ast.type == "boolean_operator": return False
    if target_ast.children[1].type != "and"     : return False

    return any(pisomorph(c, source_ast) for c in target_ast.children)


def less_specific_if(source_ast, target_ast):
    if not target_ast.type == "boolean_operator": return False
    if target_ast.children[1].type != "or"      : return False

    return any(pisomorph(c, source_ast) for c in target_ast.children)


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
        if not any(pisomorph(t, c) for t in target_ast.children):
            return False
        
    return True


def change_iterable(source_ast, target_ast):
    
    if add_elements_to_iterable(source_ast, target_ast):
        return SStubPattern.ADD_ELEMENTS_TO_ITERABLE

    return SStubPattern.SINGLE_STMT


# ADD CALL AROUND STATEMENT ----------------------------------------------------------------

def add_function_around_expression(source_ast, target_ast):
    if len(target_ast.children) == 0: return False

    argument_list = target_ast.children[-1]
    
    if argument_list.type != "argument_list":
        return False

    # It seems that adding arguments together with a function seems to be okay (see PySStuBs dataset)
    #if len(argument_list.children) != 3: return False 

    for arg in argument_list.children:
        if pisomorph(arg, source_ast):
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
    if len(target_ast.children) == 0: return False
    
    attribute = target_ast.children[0]

    if attribute.type not in ["attribute", "call"]: return False

    return pisomorph(attribute.children[0], source_ast)

# ADD attribute -------------------------------------------------------------


def add_attribute_access(source_ast, target_ast):
    if pisomorph(target_ast.children[0], source_ast):
        return SStubPattern.ADD_ATTRIBUTE_ACCESS
    
    return SStubPattern.SINGLE_STMT


# Change unary operator ----------------------------------------------------

def is_unary_operator(node):
    if "operator" not in node.type: return False
    return len(node.children) == 2


def is_unary_operator_change(source_ast, target_ast):

    if is_unary_operator(source_ast):
        for source_child in source_ast.children:
            if pisomorph(source_child, target_ast): return True
    
    if is_unary_operator(target_ast):
        for target_child in target_ast.children:
            if pisomorph(target_child, source_ast): return True

    return False
    