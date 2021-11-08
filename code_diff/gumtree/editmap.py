from apted import APTED, Config

from .utils import subtree_dice, postorder_traversal

# Minimal edit mapping to make source isomorph to target --------------------------------

# We compute a mapping between source and target tree
# If a source node is mapped to a target node with different label,
#  the source node has to be updated with the target label
# If a source node is unmapped,
#  the source node has to be deleted
# If a target node is unmapped,
#   the target node has to be added to the source tree
#
# Edits are chosen to be (approximately) minimal


# APTED for computing a minimal edit --------------------------------

class APTEDConfig(Config):

    def rename(self, node1, node2):
        
        if node1.type == node2.type:
            return 1 if node1.text != node2.text else 0

        return 1
    
    def children(self, node):
        return node.children


def _minimal_edit(isomap, source, target, max_size = 1000):
    if source.subtree_weight > max_size or target.subtree_weight > max_size: return

    apted = APTED(source, target, APTEDConfig())
    mapping = apted.compute_edit_mapping()

    for source_node, target_node in mapping:
        if source_node is None: continue
        if target_node is None: continue
        if source_node.type != target_node.type: continue

        if (source_node, None) in isomap: continue
        if (None, target_node) in isomap: continue

        yield source_node, target_node


# Select node heuristically that is close to isomorph --------------------

def _select_near_candidate(source_node, mapping):

    dst_seeds = []

    for src in source_node.descandents():
        for _, dst in mapping[src, None]:
            dst_seeds.append(dst)

    candidates = []
    seen = set()

    for dst in dst_seeds:
        while dst.parent is not None:
            parent = dst.parent
            if parent in seen: break
            seen.add(parent)

            if (parent.type == source_node.type
                    and parent.parent is not None
                    and (None, parent) not in mapping):
                candidates.append(parent)
            dst = parent

    if len(candidates) == 0: return None, 0.0

    candidates = [(x, subtree_dice(source_node, x, mapping)) for x in candidates]

    return max(candidates, key=lambda x: x[1])


# Gumtree Edit Mapping ---------------------------------------------------

def gumtree_editmap(isomap, source, target, max_size = 1000, min_dice = 0.5):
    # Caution: This method does change the isomap
    if len(isomap) == 0: return isomap

    for source_node in postorder_traversal(source):

        if source_node == source: # source_node is root
            isomap.add(source_node, target)

            for s, t in _minimal_edit(isomap, source_node, target, max_size):
                isomap.add(s, t)

            break

        if len(source_node.children) == 0: continue # source_node is leaf
        if (source_node, None) in isomap: continue  # source_node is now mapped

        target_node, dice = _select_near_candidate(source_node, isomap)

        if target_node is None or dice <= min_dice: continue 
        
        for s, t in _minimal_edit(isomap, source_node, target_node, max_size):
            isomap.add(s, t)
        isomap.add(source_node, target_node)

    return isomap