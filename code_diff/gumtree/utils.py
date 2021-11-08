from collections import defaultdict

# Collections -------------------------------------------------------------------

class NodeMapping:

    def __init__(self):
        self._src_to_dst = defaultdict(set)
        self._dst_to_src = defaultdict(set)
        self._length = 0

    def __getitem__(self, key):
        if not isinstance(key, tuple): key = (key, None)

        src_key, dst_key = key

        if src_key is not None and dst_key is not None:
            return dst_key in self._src_to_dst[src_key]

        if src_key is None and dst_key is None:
            return self.__iter__()

        if src_key is None:
            return ((src, dst_key) for src in self._dst_to_src[dst_key])
        
        if dst_key is None:
            return ((src_key, dst) for dst in self._src_to_dst[src_key])
    
    def __iter__(self):

        def _iter_maps():
            for k, V in self._src_to_dst.items():
                for v in V: yield (k, v)

        return _iter_maps()

    def __contains__(self, key):
        if not isinstance(key, tuple): key = (key, None)

        src_key, dst_key = key

        if src_key is not None and dst_key is not None:
            return self[src_key, dst_key]

        return next(self[src_key, dst_key], None) is not None

    def __len__(self):
        return self._length

    def add(self, src, dst):
        if not self[src, dst]:
            self._src_to_dst[src].add(dst)
            self._dst_to_src[dst].add(src)
            self._length += 1

    def __copy__(self):
        output = NodeMapping()

        for a, b in self:
            output.add(a, b)
        
        return output

    def __str__(self):
        approx_str = []

        for src, dst in self:
            approx_str.append("%s ≈ %s" % (str(src), str(dst)))
        
        return "\n".join(approx_str)


# Tree heuristic ----------------------------------------------------------------

def subtree_dice(A, B, mapping):

    if A is None or B is None:
        return 1.0 if all(x is None for x in [A, B]) else 0.0

    DA, DB = set(A.descandents()), set(B.descandents())

    norm = len(DA) + len(DB)

    if norm == 0: return 1.0

    mapped = defaultdict(set)
    for a, b in mapping: mapped[a].add(b)

    mapped_children = set(m for t1 in DA if t1 in mapped for m in mapped[t1])
    dice_score = len(set.intersection(mapped_children, DB))

    return 2 * dice_score / norm


# Tree traversal ----------------------------------------------------------------

def bfs_traversal(tree):
    queue = [tree]

    while len(queue) > 0: 
        node = queue.pop(0)

        yield node

        for c in node.children: 
            queue.append(c)   


def dfs_traversal(tree):
    stack = [tree]

    while len(stack) > 0: 
        node = stack.pop(-1)

        yield node

        for c in node.children: 
            stack.append(c)   


def postorder_traversal(tree):
    
    stack = [(tree, 0)]

    while len(stack) > 0:
        node, ix = stack.pop(-1)

        if ix >= len(node.children):
            yield node
        else:
            stack.append((node, ix + 1))
            stack.append((node.children[ix], 0))

