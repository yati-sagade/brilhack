from typing import List, Set
from functools import reduce
import logging

from .basic_blocks import Function


def postorder_blocks(cfg: List[List[int]]) -> List[int]:
    """Returns a post-ordering of `cfg`'s indices."""
    visited = set()
    acc = []

    def _dfs(idx):
        if idx not in visited:
            visited.add(idx)
            for succ in cfg[idx]:
                _dfs(succ)
            acc.append(idx)

    for i in range(len(cfg)):
        _dfs(i)

    return acc


def topological_sort(cfg: List[List[int]]) -> List[int]:
    return reversed(postorder_blocks(cfg))


def intersect(sets):
    if not sets:
        return set()

    ret = sets[0].copy()
    for other in sets[1:]:
        ret.intersection_update(other)
    return ret


def predecessor_map(cfg: List[List[int]]) -> List[List[int]]:
    """Returns a parallel list mapping each node to a list of its preds."""
    preds = [[] for _ in range(len(cfg))]
    for i in range(len(cfg)):
        for succ in cfg[i]:
            preds[succ].append(i)
    return preds


def dominators(cfg: List[List[int]]) -> List[Set[int]]:
    """Returns the dominators for cfg as a parallel list."""
    blocks = list(topological_sort(cfg))
    nblock = len(blocks)
    allblocks = set(range(nblock))
    dom = [allblocks.copy() if i != 0 else {0} for i in range(nblock)]
    more = True
    preds = predecessor_map(cfg)
    niter = 0
    while more:
        print('iter {}: {}'.format(niter, dom))
        more = False
        niter += 1
        for i in range(nblock):
            if not preds[i]:
                continue
            d = intersect([dom[p] for p in preds[i]])
            d.add(i)
            if d != dom[i]:
                dom[i] = d
                more = True
    logging.debug('dominator_tree took {} iters'.format(niter))
    return dom


def dominator_tree(cfg: List[List[int]]) -> List[Set[int]]:
    """Returns the dominator tree for cfg as a parallel list."""
    preds = predecessor_map(cfg)
    all_doms = dominators(cfg)
    domtree = [set() for _ in range(len(cfg))]
    for idx, doms in enumerate(all_doms):
        # Domtree parent is the predecessor which is a dominator.
        # Note that we cannot have all predecessors dominating a node.
        parent = doms.intersection(preds[idx])
        assert len(
            parent
        ) <= 1, 'For node {}, multiple domination tree parent candidates ({}) found! doms={}, preds={}'.format(
            idx, parent, doms, preds[idx])
        if parent:
            domtree[parent.pop()].add(idx)
    return domtree
