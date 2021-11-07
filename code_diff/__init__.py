from .ast import parse_ast


# Main method --------------------------------------------------------

def difference(source, target, lang = "guess", **kwargs):
    
    source_ast = parse_ast(source, lang = lang, **kwargs)
    target_ast = parse_ast(target, lang = lang, **kwargs)

    # Concretize Diff
    source_ast, target_ast = diff_search(source_ast, target_ast)

    return ASTDiff(source_ast, target_ast)


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

    def __init__(self, source_ast, target_ast):
        self.source_ast = source_ast
        self.target_ast = target_ast