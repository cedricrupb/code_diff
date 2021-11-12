
import heapq
import itertools
import math

from collections import defaultdict

from .utils import NodeMapping, subtree_dice

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


def source_distance(source_node, target_node):
   
    max_token_mover = 1000

    line_mover_distance = source_node.position[0][0] - target_node.position[1][0]
    line_mover_distance = line_mover_distance * max_token_mover

    if line_mover_distance == 0:
        token_mover_distance = min(abs(source_node.position[0][1] - target_node.position[0][1]), max_token_mover - 1) 
        line_mover_distance += token_mover_distance

    return -line_mover_distance



def create_default_heuristic(isomorphic_mapping):

    def _heuristic(source_node, target_node):
        return (subtree_dice(source_node, target_node, isomorphic_mapping), source_distance(source_node, target_node))
    
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

