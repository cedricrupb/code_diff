import code_tokenize as ct

from collections import defaultdict

# AST Node ----------------------------------------------------------------


class ASTNode(object):
    """
    A representation of an AST node together with its children

    Node Attributes
    ---------------
    type : str
        Syntactic type of the AST node

    text : str
        If this node belongs to a program token, then
        it contains the text of the program token. Otherwise, None.
    
    children : list[ASTNode]
        Potenially empty list of child nodes
    
    position : int
        If supported, the code position that is referenced by the AST node

    parent : ASTNode
        If not root node, the AST parent of this node.
    
    Subtree Attributes
    ------------------
    subtree_hash : str
        A hash string representing the subtree of the AST node
        Two subtrees are isomorph if they have the same subtree hash.
    
    subtree_height : int
        Longest path from this node to a leaf node

    subtree_weight : int
        Count of all nodes in this subtree
    
    """

    def __init__(self, type, text = None, position = None, parent = None, children = None):

        # Basic node attributes
        self.type = type
        self.children = children if children is not None else []
        self.parent   = parent
        self.text     = text   # If text is not None, then leaf node
        self.position = position

        # Tree based attributes
        self.subtree_hash      = None
        self.subtree_height    = 1
        self.subtree_weight    = 1

    def isomorph(self, other):
        return ((self.subtree_hash, self.type, self.subtree_height, self.subtree_weight) == 
                    (other.subtree_hash, other.type, other.subtree_height, other.subtree_weight))

    def descandents(self):
        return (t for t in self if t != self) 

    def sexp(self):
        name = self.text if self.text is not None else self.type

        child_sexp = []
        for child in self.children:
            text = child.sexp()
            text = ["  " + t for t in text.splitlines()]
            child_sexp.append("\n".join(text))
        
        if len(child_sexp) == 0:
            return name

        return "%s {\n%s\n}" % (name, " ".join(child_sexp))
        
    def __iter__(self):
        def _self_bfs_search():
            queue = [self]
            while len(queue) > 0:
                current = queue.pop(0)
                yield current
                queue.extend(current.children)

        return _self_bfs_search()

    def __repr__(self):
        attrs = {"type": self.type, "text": self.text}
        return "ASTNode(%s)" % (", ".join(["%s=%s" % (k, v) for k, v in attrs.items() if v is not None]))


def default_create_node(type, children, text = None, position = None):
    new_node = ASTNode(type, text = text, position = position, children = children)

    # Subtree metrics
    height = 1
    weight = 1
    hash_str = []

    for child in children:
        child.parent = new_node # Set parent relation
        height       = max(child.subtree_height + 1, height)
        weight      += child.subtree_weight
        hash_str.append(str(child.subtree_hash))
    
    new_node.subtree_height = height
    new_node.subtree_weight = weight

    # WL hash subtree representation
    base_str = new_node.type if new_node.text is None else new_node.text
    hash_str.insert(0, base_str)
    hash_str = "_".join(hash_str)
    new_node.subtree_hash = hash(hash_str)

    return new_node


def _node_key(node):
    return (node.type, node.start_point, node.end_point)


class TokensToAST:

    def __init__(self, create_node_fn):
        self.create_node_fn = create_node_fn

        self.root_node = None
        self.waitlist = []
        self.node_index = {}
        self.child_count = defaultdict(int)

    def _create_node(self, ast_node, text = None):

        if ast_node.type == "comment": return # We ignore comments

        node_key = _node_key(ast_node)
        children = [self.node_index[_node_key(c)] for c in ast_node.children
                     if _node_key(c) in self.node_index]

        position = (ast_node.start_point, ast_node.end_point)
        current_node = self.create_node_fn(ast_node.type, children, text = text, position = position)
        current_node.backend = ast_node

        self.node_index[node_key] = current_node

        # Add parent if ready
        if ast_node.parent:
            parent_ast = ast_node.parent
            parent_key = _node_key(parent_ast)
            self.child_count[parent_key] += 1

            if len(parent_ast.children) == self.child_count[parent_key]:
                self.waitlist.append(parent_ast)

        else:
            self.root_node = current_node


    def _open_node(self, node):
        node_key = _node_key(node)
        if node_key in self.node_index: return False

        opened = False
        for c in node.children:
            opened = opened or self._open_node(c)
        
        if not opened:
            self.waitlist.append(node)
            return True
        
        return False

    def _open_root_if_not_complete(self, base_node):
        
        root = base_node
        while root.parent is not None:
            root = root.parent
        
        for c in root.children:
            self._open_node(c)

    def __call__(self, tokens):
        
        token_nodes = ((t.text, t.ast_node) for t in tokens if hasattr(t, "ast_node"))
        for token_text, token_ast in token_nodes:
            self._create_node(token_ast, text = token_text)

        while self.root_node is None:
            while len(self.waitlist) > 0:
                current_node = self.waitlist.pop(0)
                self._create_node(current_node)

            self._open_root_if_not_complete(current_node)

        print(self.root_node.sexp())
        
        return self.root_node



class BottomUpParser:

    def __init__(self, create_node_fn):
        
        self.create_node_fn = create_node_fn
        self.waitlist    = [] # Invariant: All children have been processed
        self.open_index  = {} 
        self.node_index  = {} # Nodes that have been processed

    def _should_ignore(self, node):
        return node.type == "comment"

    def _add_to_waitlist(self, node):
        if self._should_ignore(node): return

        node_key = _node_key(node)

        if node_key not in self.node_index and node_key not in self.open_index:
            self.open_index[node_key] = node
            self.waitlist.append(node)


    def _init_lists(self, tokens):
        
        for token in tokens:
            if hasattr(token, 'ast_node'):
                ast_node = token.ast_node
                if self._should_ignore(ast_node): continue
                self.open_index[_node_key(ast_node)] = ast_node
                self._create_node(ast_node, token.text)

        if ast_node is None: return

        # Get to root
        root = ast_node
        while root.parent is not None:
            root = root.parent

        self._open_descandents(root)

        return root

    def _open_descandents(self, node):

        queue = [node]
        while len(queue) > 0:
            current_node = queue.pop(0)

            has_opened = False
            for child in current_node.children:
                if _node_key(child) not in self.node_index:
                    has_opened = True
                    queue.append(child)
            
            if not has_opened: 
                self._add_to_waitlist(current_node)


    def _open_parent(self, ast_node):
        parent = ast_node.parent

        if all(_node_key(c) in self.node_index for c in parent.children if not self._should_ignore(c)):
            self._add_to_waitlist(parent)

    def _create_node(self, ast_node, text = None):

        node_key = _node_key(ast_node)
        children = [self.node_index[_node_key(c)] for c in ast_node.children
                     if _node_key(c) in self.node_index]

        position = (ast_node.start_point, ast_node.end_point)
        current_node = self.create_node_fn(ast_node.type, children, text = text, position = position)
        current_node.backend = ast_node

        self.node_index[node_key] = current_node
        del self.open_index[node_key]
        
        if ast_node.parent: self._open_parent(ast_node)


    def __call__(self, tokens):
        root_node = self._init_lists(tokens)

        while len(self.waitlist) > 0:
            self._create_node(self.waitlist.pop(0))
        
        if _node_key(root_node) not in self.node_index:
            return None

        return self.node_index[_node_key(root_node)]


    

# Interface ----------------------------------------------------------------


def parse_ast(source_code, lang = "guess", **kwargs):
    """
    Parses a given source code string into its AST

    Function to parse source code in the given language
    into its AST. As a backend, we employ
    code_tokenize (tree-sitter). The final
    AST is additionally analyzed to compute
    additional annotations

    Parameters
    ----------
    source_code : str
        Source code snippet as a string
    
    lang : [python, java, javascript, ...]
        Language to parse the given source code
        Default: guess (Currently not supported; will raise error)

    Returns
    -------
    ASTNode
        the root node of the computed AST
    
    """
    
    # Parse AST 
    kwargs["lang"] = lang
    kwargs["syntax_error"] = "ignore"

    ast_tokens = ct.tokenize(source_code, **kwargs)
    
    return BottomUpParser(default_create_node)(ast_tokens)