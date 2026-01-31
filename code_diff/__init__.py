from code_tokenize.lang import load_from_lang_config
from code_tokenize.tokens import match_type

from .ast     import parse_ast
from .utils   import cached_property
from .sstubs  import SStubPattern, classify_sstub
from .gumtree import compute_edit_script, EditScript, Update
from .gumtree import diff_search_with_isomap, compute_isomap

from .gumtree.ops import Insert, Move, Delete, Update

from collections import namedtuple


# Main method --------------------------------------------------------

def difference(source, target, lang = "guess", **kwargs):
    """
    Computes the smallest difference between source and target

    Computes the smallest code difference between the given 
    code snippets. Difference is computed by a simulteanous
    walk over the ASTs of the given code snippets. Returned
    will be the smallest code snippet that represent
    the first AST node found to be different.

    Parameters
    ----------
    source : str
        Source code which should be compared
    
    target : str
        Comparison target as a code string

    lang : [python, java, javascript, ...]
        Programming language which should be used
        to parse the code snippets.
        Default: guess (Currently not supported, will throw error)
    
    syntax_error : [raise, warn, ignore]
        Strategy to handle syntax errors in code.
        To parse incomplete code snippets, 'ignore' should
        be selected to silent any warning.
        Default: raise (Raises an exception)

    **kwargs : dict
        Further config option that are specific to
        the underlying AST parser. See code_tokenize
        for more infos.

    Returns
    -------
    ASTDiff
        The smallest code change necessary
        to convert the source code into the target code.
    
    """
    
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
    """
    Difference between two code snippets

    This object represents the smallest code change
    necessary to transform a source code snippet
    into a target code.

    Attributes
    ----------
    is_single_statement : bool
        Whether the code difference only affect a single program statement

    source_ast : ASTNode
        AST node related to the code change
    
    source_text : str
        Source code which have to be changed

    target_ast : ASTNode
        AST node which is different to the source AST

    target_text : str
        Target text for converting source to target
    
    Methods
    -------
    edit_script : list[EditOp]
        Computes a sequence of AST operations which need
        to be performed to translate source code in target code
        
        Note: We balance performance and precision by computing
        the AST edit script at the current diff level. The
        algorithm runs the fastest on the smallest diff level
        but is also most imprecise. To achieve the highest precision,
        the root_diff should be used.

    sstub_pattern : SStuBPattern
        Categorizes the current diff into one of 20 SStuB categories.
        Note: Currently, this operation is only supported for
        Python code. Running the function on code in another language
        will cause an exception.

    statement_diff : ASTDiff
        raises the AST difference to the statement level
    
    root_diff : ASTDiff
        raises the AST difference to the root level (of each code snippet)

    
    """

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

    def root_diff(self):
        return ASTDiff(self.config, ast_root(self.source_ast), ast_root(self.target_ast))

    def sstub_pattern(self):
        if self.config.lang != "python":
            raise ValueError("SStuB can currently only be computed for Python code.")
        
        if (parent_statement(self.config.statement_types, self.source_ast) is None
                or parent_statement(self.config.statement_types, self.target_ast) is None):
            return SStubPattern.NO_STMT                

        if not self.is_single_statement:
            return SStubPattern.MULTI_STMT
        
        return classify_sstub(*diff_search(self.source_ast, self.target_ast))

    def edit_script(self):

        source_ast, target_ast = self.source_ast, self.target_ast

        if source_ast.type == target_ast.type and len(source_ast.children) == 0 and len(target_ast.children) == 0:
            # Both nodes are tokens of the same type 
            # Only an update is required
            return EditScript([Update(source_ast, target_ast.text)])

        # We need a common root to add to
        while True: 
            if source_ast.parent is None: break
            if target_ast.parent is None: break

            source_ast = source_ast.parent
            target_ast = target_ast.parent
            if source_ast.type == target_ast.type: break

        return compute_edit_script(source_ast, target_ast)

    def apply(self, other : str):
        source_ast      = ast_root(self.source_ast)
        other_ast_root  = parse_ast(other, lang = self.config.lang, 
                                        syntax_error = self.config.syntax_error)
        
        source_ast, other_ast, src_to_oth = diff_search_with_isomap(source_ast, other_ast_root)
        if source_ast is not None:
            for src, oth in compute_isomap(source_ast, other_ast):
                src_to_oth.add(src, oth)

        # --- So far, mapping from src -> other ----
    
        inserted_nodes = {}
        def _map_node(src_node):
            if hasattr(src_node, "node_id") and src_node.node_id in inserted_nodes:
                return inserted_nodes[src_node.node_id]
            
            if (src_node, None) not in src_to_oth:
                raise ValueError(f"{src_node} has been deleted. Cannot perform the update.")

            for _, oth_node in src_to_oth[(src_node, None)]:
                return oth_node


        for op in self.edit_script():
            target_node = _map_node(op.target_node)

            if isinstance(op, Move):
                move_node = _map_node(op.node)
                op.map(target_node, move_node).apply()

            elif isinstance(op, Insert):
                reverse_op = op.map(target_node).apply()
                inserted_nodes[op.insert_id] = reverse_op.target_node

            elif isinstance(op, Delete):
                reverse_op = op.map(target_node).apply()
                # Should we update the isomap here?
            else:
                op.map(target_node).apply()
        

        # Minimize the edit to be performed
        old_other = parse_ast(other, lang = self.config.lang, 
                               syntax_error = self.config.syntax_error)
        
        old_ast, new_ast = diff_search(old_other, other_ast_root)    
        return _apply_ast_edits(other, old_ast, new_ast), ASTDiff(self.config, new_ast, old_ast)

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


def ast_root(ast):
    parent_node = ast

    while parent_node.parent is not None:
        parent_node = parent_node.parent

    return parent_node


def tokenize_tree(ast):
    tokens = []

    # Test if any other statement as child
    if ast.text: tokens.append(ast.text)

    for child in ast.children:
        tokens.append(tokenize_tree(child))
    
    return " ".join(tokens)


Position = namedtuple("Point", ["row", "column"])

def _compute_offsets(text):
    lines = text.splitlines(True)
    if len(lines) == 1:
        return 0, len(lines[0])
    else:
        return len(lines), len(lines[-1])

def tree_to_code(ast):
    tokens = []

    if ast.text: tokens.append(ast.text)

    last_element = None
    for child in ast.children:
        code_string = tree_to_code(child)
        
        if last_element and not child.position:
            last_end    = last_element.position[1]
            start = Position(last_end.row, last_end.column + 1)

            row_offset, column_offset = _compute_offsets(code_string)
            if row_offset == 0:
                child.position = (start, 
                                  Position(start.row, start.column + column_offset))
            else:
                child.position = (start, Position(start.row + row_offset, column_offset))

        if last_element:
            last_end    = last_element.position[1]

            if child.position:
                child_start = child.position[0]

                if last_end.row == child_start.row:
                    tokens.append(" "*(child_start.column - last_end.column))
                else:
                    tokens.append("\n"*(child_start.row - last_end.row) + " "*child_start.column)

        tokens.append(code_string)
        last_element = child

    return "".join(tokens)



def is_compatible_root(root_candidate, source_ast):
    return not equal_text(source_ast, root_candidate) and root_candidate.type != "block"


def equal_text(source_ast, parent_ast):
    source_position = source_ast.position
    parent_position = parent_ast.position

    if parent_position[0][0] < source_position[0][0]: return False
    if source_position[1][0] < parent_position[1][0]: return False

    return (source_position[0][1], source_position[1][1]) == (parent_position[0][1], parent_position[1][1])


def _apply_edits(source_text, edits):
    source_lines = source_text.splitlines(True)
    
    normed_edits = []
    for position, text in edits:
        position = (position[0].row, position[0].column, position[1].row, position[1].column)
        normed_edits.append((position, text))

    for (pos, text) in sorted(normed_edits)[::-1]:
        if pos[0] == pos[2]:
            source_lines[pos[0]] = source_lines[pos[0]][:pos[1]] + text + source_lines[pos[0]][pos[3]:]
        else:
            source_lines[pos[0]:pos[2]+1] = [source_lines[pos[0]][:pos[1]]] + [text] +  [source_lines[pos[2]][pos[3]:]]

    return "".join(source_lines)


def _apply_ast_edits(source_text, source_node, target_node):
    if source_node is None or source_node.isomorph(target_node): return source_text

    edits = []
    queue = [(source_node, target_node)]
    while len(queue) > 0:
        source_node, target_node = queue.pop(0)

        if len(source_node.children) != len(target_node.children):
            edits.append((source_node.position, tree_to_code(target_node)))
            continue

        for i, source_child in enumerate(source_node.children):
            target_child = target_node.children[i]

            if not source_child.isomorph(target_child):
                if source_child.position[0].row == source_child.position[1].row:
                    edits.append((source_child.position, tree_to_code(target_child)))
                else:
                    queue.append((source_child, target_child))

    return _apply_edits(source_text, edits)