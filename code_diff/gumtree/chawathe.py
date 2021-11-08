import itertools

from .ops   import Update, Insert, Delete, Move
from .utils import bfs_traversal, postorder_traversal

# API method ----------------------------------------------------------------

def compute_chawathe_edit_script(editmap, source, target):

    edit_script = []

    source_root, source_parent = _fake_root(source)
    target_root, target_parent = _fake_root(target)
    editmap.add(source_root, target_root)

    wt = WorkingTree(editmap)
    wt[source].mod_parent = wt[source_root] # Inject fake root only for working copy

    for target_node in bfs_traversal(target): 

        if target_node == target: # Script might start in the middle of AST
            parent = target_root
        else:
            parent = target_node.parent

        if parent is None: parent = target_root

        source_partner = wt.partner(target_node)
        parent_partner = wt.partner(parent)

        if source_partner is None:
            k = wt.position(target_node)
            op = Insert(
                    parent_partner.delegate,
                    (target_node.type, target_node.text),
                    k,
                    -1
                )
            edit_script.append(op)
            node = parent_partner.apply(op)
            editmap.add(node, target_node)
        
        elif target_node.parent is not None:

            if target_node.text is not None and source_partner.text != target_node.text:
                op = Update(source_partner.delegate, target_node.text)
                edit_script.append(op)
                source_partner.apply(op)
            
            partner_parent = source_partner.parent

            if not editmap[partner_parent.delegate, parent]:
                k = wt.position(target_node)
                op = Move(
                    parent_partner.delegate,
                    source_partner.delegate,
                    k
                )
                edit_script.append(op)
                parent_partner.apply(op)
        
        target_node.inorder = True
        for move in _align_children(wt.partner(target_node), target_node, wt):
            edit_script.append(move)

    for node in postorder_traversal(source):
        node = wt[node]
        partner = node.partner
        if partner is None:
            op = Delete(node.delegate)
            edit_script.append(op)
            node.apply(op)

    # Change root back after edit
    source.parent = source_parent
    target.parent = target_parent

    return edit_script


# Alignment ------------------------------------------------------------------

def _longest_common_subsequence(source, target, equal_fn):

    lengths = [[0] * (len(target)+1) for _ in range(len(source)+1)]
    for i, x in enumerate(source):
        for j, y in enumerate(target):
            if equal_fn(x, y):
                lengths[i+1][j+1] = lengths[i][j] + 1
            else:
                lengths[i+1][j+1] = max(lengths[i+1][j], lengths[i][j+1])

    result = []

    # Backtrack
    i, j = len(source), len(target)
    while i > 0 and j > 0:
        if equal_fn(source[i - 1], target[j - 1]):
            result.append((source[i - 1], target[j - 1]))
            i -= 1
            j -= 1
        else:
            if lengths[i][j - 1] > lengths[i - 1][j]:
                j -= 1
            elif lengths[i][j - 1] == lengths[i - 1][j]:
                # Heuristic we like to select terminal nodes for LCS

                if source[i - 1].text is None:
                    i -= 1
                else:
                    j -= 1

            else:
                i -= 1
 
    return result[::-1]


def _align_children(source, target, wt):
    for c in source.children: c.inorder = False
    for c in target.children: c.inorder = False

    def _partner_child(c, o, src_partner = False):
        p = wt.partner(c) if src_partner else c.partner
        if p is None: return False
        return p.parent == o

    S1 = [c for c in source.children if _partner_child(c, target)]
    S2 = [c for c in target.children if _partner_child(c, source, True)]

    S = _longest_common_subsequence(S1, S2, lambda x, y: wt.isomap[x.delegate, y])

    SM = set()

    for a, b in S:
        a.inorder = True
        b.inorder = True
        SM.add((a, b))

    for a, b in itertools.product(S1, S2):
        if wt.isomap[a.delegate, b] and (a, b) not in SM:
            k = wt.position(b)
            op = Move(a.delegate, source.delegate, k)
            yield op
            source.apply(op)
            a.inorder = True
            b.inorder = True

# Working tree ----------------------------------------------------------------
# A tree to capture all AST modifications during edit

class InsertNode:

    INSERT_COUNT = 0

    def __init__(self, type, text = None, children = None):
        self.type = type
        self.text = text

        self.node_id = InsertNode.INSERT_COUNT
        InsertNode.INSERT_COUNT += 1

        self.parent = None 
        self.children = children if children is not None else []

    def __repr__(self):
        output = {"type": self.type, "text": self.text}
        return "IN(%s)" % ", ".join(["%s=%s" % (k, v) for k, v in output.items() if v is not None])


def _fake_root(root):
    node = InsertNode("root", None, [root])
    node.parent = None

    old_parent = root.parent
    root.parent = node

    return node, old_parent


class WorkingNode:

    def __init__(self, src, delegate):
        self.src = src
        self.delegate = delegate

        self.text = self.delegate.text
        self.mod_parent = None
        self.mod_children = None

        self.mod_partner = None

    @property
    def parent(self):

        if self.mod_parent is None:
            self.mod_parent = self.src._access_wn(self.delegate.parent)

        return self.mod_parent

    @property
    def children(self):
        if self.mod_children is None:
            self.mod_children = [self.src._access_wn(c) for c in self.delegate.children]

        return self.mod_children


    @property
    def partner(self):

        if self.mod_partner is None:
            node = self.delegate

            if node is None: return None

            result = self.isomap[node, None]
            result = next(result, None)

            if result is None: return None

            self.mod_partner = result[1]

        return self.mod_partner

    @property
    def isomap(self):
        return self.src.isomap


    def apply(self, operation):
        
        if isinstance(operation, Insert):
            node = InsertNode(*operation.node)
            operation.insert_id = node.node_id
            wn   = self.src._access_wn(node)
            self.children.insert(operation.position, wn)

            node.parent = self.delegate

            return node
        
        if isinstance(operation, Update):
            self.text = operation.value
            return

        if isinstance(operation, Delete):
            node = operation.target_node
            node = self.src._access_wn(node)

            for n, child in enumerate(node.parent.children):
                if child == node: break
        
            del node.parent.mod_children[n]
            return

        if isinstance(operation, Move):
            insert_node = operation.node 

            self.apply(Delete(insert_node))

            wn   = self.src._access_wn(insert_node)
            self.mod_children.insert(operation.position, wn)

            wn.mod_parent = self

            return insert_node


class WorkingTree:

    def __init__(self, isomap):
        self.isomap = isomap
        self.node_to_wn = {}

    def _access_wn(self, source_node):
        if source_node is None: return None

        if isinstance(source_node, WorkingNode):
            return source_node

        if source_node not in self.node_to_wn:
            self.node_to_wn[source_node] = WorkingNode(self, source_node)

        return self.node_to_wn[source_node]

    def __getitem__(self, key):
        return self._access_wn(key)


    def partner(self, target_node): 
        if target_node is None: return None

        result = self.isomap[None, target_node]
        result = next(result, None)

        if result is None: return None

        source_node = result[0]
        wn = self._access_wn(source_node)
        wn.mod_partner = target_node
        return wn

    def position(self, target_node):
        parent = target_node.parent

        if parent is None: return 0

        for n, child in enumerate(parent.children):
            if child == target_node: break

        if all(not c.inorder for c in parent.children[:n]):
            return 0

        left_child = parent.children[n - 1]
        while not left_child.inorder:
            n -= 1
            left_child = parent.children[n - 1]

        left_partner = self.partner(left_child)
    
        for n, child in enumerate(left_partner.parent.children):
            if child == left_partner: break

        return sum(1 for c in parent.children[:n] if c.inorder) + 1
