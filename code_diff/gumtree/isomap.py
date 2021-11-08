
import heapq
import itertools

from collections import defaultdict

# API method ----------------------------------------------------------------

def gumtree_isomap(source_ast, target_ast, min_height = 1):

    isomorphic_mapping = NodeMapping()
    candidate_mapping  = NodeMapping()

    source_index = _index_iso_nodes(source_ast)
    target_index = _index_iso_nodes(target_ast)

    source_open = HeightPriorityHeap(source_ast)
    target_open = HeightPriorityHeap(target_ast)

    while max(source_open.max(), target_open.max()) > min_height:

        if source_open.max() > target_open.max():
            for c in list(source_open.pop()):
                _open_node(source_open, c)
            continue
            
        if source_open.max() < target_open.max():
            for c in list(target_open.pop()):
                _open_node(target_open, c)
            continue

        source_candidates, target_candidates = list(source_open.pop()), list(target_open.pop())

        for source_node, target_node in itertools.product(source_candidates, target_candidates):
            # Source node and Target node have the same height
            # Check if source node is isomorph to target node

            if source_node.isomorph(target_node):
                # Check if there exists more candidates
                if (source_index[source_node] > 1
                        or target_index[target_node] > 1):
                        candidate_mapping.add(source_node, target_node)
                else:
                    # We can savely map both nodes and all descandents
                    _map_recursively(isomorphic_mapping, source_node, target_node)

        # Open all unmapped nodes
        for source_node in source_candidates:
            if ((source_node, None) not in isomorphic_mapping
                and (source_node, None) not in candidate_mapping):
                _open_node(source_open, source_node)

        for target_node in target_candidates:
            if ((None, target_node) not in isomorphic_mapping
                and (None, target_node) not in candidate_mapping):
                _open_node(target_open, target_node)

    # Select the heuristically best mapping for all isomorphic pairs
    selection_heuristic = create_default_heuristic(isomorphic_mapping)
    for source_node, target_node in _select_candidates(candidate_mapping, selection_heuristic):
        _map_recursively(isomorphic_mapping, source_node, target_node)

    return isomorphic_mapping


# Collections ----------------------------------------------------------------

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


class NodeCounter:

    def __init__(self):
        self._counter = defaultdict(int)

    def _node_key(self, node):
        return (node.subtree_hash, node.subtree_weight)

    def __getitem__(self, node):
        return self._counter[self._node_key(node)]
    
    def __setitem__(self, node, value):
        self._counter[self._node_key(node)] = value


class HeightPriorityHeap:

    def __init__(self, start_node = None):
        self._heap = []
        self.element_count = 0

        if start_node is not None:
            self.push(start_node)

    def __len__(self):
        return len(self._heap)

    def push(self, x, seed = 0):
        try:
            heapq.heappush(self._heap, (-x.subtree_height, x.subtree_hash, self.element_count, seed, x))
            self.element_count += 1
        except TypeError:
            # Typically the type error occurs if we compare with the last element in tuple (Node)
            # If this happens the node is already contained in the heap and we skip this push
            return
    
    def max(self):
        if len(self) == 0: return 0
        return -self._heap[0][0]

    def pop(self):
        current_head = self.max()

        while len(self) > 0 and self.max() == current_head:
            yield heapq.heappop(self._heap)[-1]

# Helper methods -----------------------------------------------------------

def _index_iso_nodes(ast):
    result = NodeCounter()
    for node in ast: result[node] += 1

    return result

def _open_node(heap, node):
    for n, child in enumerate(node.children):
        heap.push(child, seed = n)

def _map_recursively(mapping, source_node, target_node):
    mapping.add(source_node, target_node)

    for i, source_child in enumerate(source_node.children):
        target_child = target_node.children[i]
        assert source_node.type == target_node.type

        _map_recursively(mapping, source_child, target_child)

# Heuristic selection ----------------------------------------------------------------

def _subtree_dice(A, B, mapping):

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


def create_default_heuristic(isomorphic_mapping):

    def _heuristic(source_node, target_node):
        dice = _subtree_dice(source_node, target_node, isomorphic_mapping)
        return dice
    
    return _heuristic


def _select_candidates(candidate_mapping, heuristic = None):
    if len(candidate_mapping) == 0: return

    candidate_pairs = [(s, t) for s, t in candidate_mapping]

    if heuristic is not None:
        candidate_pairs = sorted(candidate_pairs, 
                                    key=lambda p: heuristic(*p), 
                                    reverse=True)
    
    source_seen = set()
    target_seen = set()

    while len(candidate_pairs) > 0:
        source_node, target_node = candidate_pairs.pop(0)

        if source_node in source_seen:
            continue
        source_seen.add(source_node)

        if target_node in target_seen:
            continue
        target_seen.add(target_node)
        
        yield source_node, target_node

