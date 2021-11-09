from code_tokenize.config import load_from_lang_config
from code_tokenize.tokens import match_type

from .ast     import parse_ast
from .utils   import cached_property
from .sstubs  import SStubPattern, classify_sstub
from .gumtree import compute_edit_script


# Main method --------------------------------------------------------

def difference(source, target, lang = "guess", **kwargs):
    
    config     = load_from_lang_config(lang, **kwargs)
    source_ast = parse_ast(source, lang = lang, **kwargs)
    target_ast = parse_ast(target, lang = lang, **kwargs)

    if source_ast is None or target_ast is None:
        raise ValueError("Source / Target AST seems to be empty: %s" % source)

    # Concretize Diff
    source_ast, target_ast = diff_search(source_ast, target_ast)

    if source_ast is None:
        raise ValueError("Source and Target AST are identical.")

    return ASTDiff(config, source_ast, target_ast)


# Diff Search --------------------------------------------------------
# Run BFS until we find a node with at least two diffs

def diff_search(source_ast, target_ast):
    if source_ast is None or source_ast.isomorph(target_ast): return None, None

    queue = [(source_ast, target_ast)]
    while len(queue) > 0:
        source_node, target_node = queue.pop(0)

        if len(source_node.children) != len(target_node.children):
            return (source_node, target_node)
        
        next_children = []
        for i, source_child in enumerate(source_node.children):
            target_child = target_node.children[i]

            if not source_child.isomorph(target_child): 
                next_children.append((source_child, target_child))
        
        if len(next_children) == 1:
            queue.append(next_children[0])
        else:
            return (source_node, target_node)


# AST Difference --------------------------------------------------------

class ASTDiff:

    def __init__(self, config, source_ast, target_ast):
        self.config     = config
        self.source_ast = source_ast
        self.target_ast = target_ast

    @cached_property
    def is_single_statement(self):
        return (is_single_statement(self.config.statement_types, self.source_ast)
                    and is_single_statement(self.config.statement_types, self.target_ast))

    @cached_property
    def source_text(self):
        return tokenize_tree(self.source_ast)

    @cached_property
    def target_text(self):
        return tokenize_tree(self.target_ast)

    def statement_diff(self):
        source_stmt = parent_statement(self.config.statement_types, self.source_ast)
        target_stmt = parent_statement(self.config.statement_types, self.target_ast)

        if source_stmt is None or target_stmt is None: 
            raise ValueError("AST diff is not enclosed in a statement")
        
        return ASTDiff(self.config, source_stmt, target_stmt)

    def sstub_pattern(self):
        if (parent_statement(self.config.statement_types, self.source_ast) is None
                or parent_statement(self.config.statement_types, self.target_ast) is None):
            return SStubPattern.NO_STMT                

        if not self.is_single_statement:
            return SStubPattern.MULTI_STMT
        
        return classify_sstub(*diff_search(self.source_ast, self.target_ast))

    def edit_script(self):

        source_ast, target_ast = self.source_ast, self.target_ast

        def is_statement_type(node_type):
            return any(match_type(r, node_type) for r in self.config.statement_types)

        if not is_statement_type(source_ast.type) or not is_statement_type(target_ast.type):
            # We need something where we can add to (root)
            if source_ast.parent is not None:
                source_ast = source_ast.parent
            
            if target_ast.parent is not None:
                target_ast = target_ast.parent

        return compute_edit_script(source_ast, target_ast)

    def __repr__(self):
        return "%s -> %s" % (self.source_text, self.target_text)

    


# AST Utils -----------------------------------------------------------

def is_single_statement(statement_types, ast):

    if parent_statement(statement_types, ast) is None: return False
        
    def is_statement_type(node_type):
        return any(match_type(r, node_type) for r in statement_types)

    # Test if any other statement as child
    queue = list(ast.children)
    while len(queue) > 0:
        node = queue.pop(0)
        if is_statement_type(node.type): return False

        queue.extend(node.children)
    
    return True


def parent_statement(statement_types, ast):
    
    def is_statement_type(node_type):
        return any(match_type(r, node_type) for r in statement_types)

    # Test if node in statement
    parent_node = ast
    while parent_node is not None and not is_statement_type(parent_node.type):
        parent_node = parent_node.parent
    
    return parent_node


def tokenize_tree(ast):
    tokens = []

    # Test if any other statement as child
    if ast.text: tokens.append(ast.text)

    for child in ast.children:
        tokens.append(tokenize_tree(child))
    
    return " ".join(tokens)
