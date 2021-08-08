from typing import List, Set
from functools import reduce
import logging
from collections import deque

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
        logging.debug('finding dominators iter {}: {}'.format(niter, dom))
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


class NotANaturalLoop(Exception):
    pass


def _extract_loop(cfg: List[List[int]], doms, preds, header, loopback):
    """Given the header and a loopback node that there is a loopback->header
  back-edge in `cfg`, returns the minimal set of nodes in `cfg` L such that

    1. loopback and header are in L.
    2. If a given node n is in L, and n != header, preds(n) are all also in L.
  """
    if header not in doms[loopback]:
        raise NotANaturalLoop('{} is not dominated by header {}'.format(
            loopback, header))
    # If a node A dominates B, it also dominates each of preds[B].
    # Since header dominates loopback, it also dominates all its preds and
    # preds of those preds, etc.
    loop = set()
    q = deque([loopback])
    while q:
        node = q.popleft()
        loop.add(node)
        if node == header:
            continue
        assert header in doms[node],\
          'Expected {} to be dominated by header {}'.format(node, header)
        for pred in preds[node]:
            if pred not in loop:
                q.append(pred)
    return loop


def _dfs_cfg(cfg: List[List[int]],
             on_node_visit=None,
             on_node_process=None,
             on_back_edge=None):
    """Runs DFS on the given CFG.

    Calls:
      - on_node_visit(cfg, dominators, predecessors, node) the first time a
      node is encountered.
      - on_node_process(cfg, dominators, predecessors, node) when the DFS
      for a node has finished.
      - on_back_edge(cfg, dominators, predecessors, head, tail) for each
      back-edge (tail->head).

      In the above callbacks,
      * dominators[i]: set = dominators of node i,
      * predecessors[i]: list = preds of node i,
    """

    visited = set()
    processed = set()
    doms = dominators(cfg)
    preds = predecessor_map(cfg)

    def _dfs(idx):
        visited.add(idx)
        if on_node_visit is not None:
            on_node_visit(cfg, doms, preds, idx)
        for succ in cfg[idx]:
            if succ not in visited:
                _dfs(succ)
            elif (succ in visited and succ not in processed
                  and on_back_edge is not None):
                on_back_edge(cfg, doms, preds, succ, idx)
        processed.add(idx)
        if on_node_process is not None:
            on_node_process(cfg, doms, preds, idx)

    for i in range(len(cfg)):
        _dfs(i)


def extract_natural_loops(cfg: List[List[int]]) -> List[List[int]]:
    """Returns all natural loops in `cfg`."""
    loops = []

    def on_back_edge(cfg, doms, preds, header, curr):
        try:
            loop = _extract_loop(cfg, doms, preds, header, curr)
            loops.append(loop)
        except NotANaturalLoop:
            pass

    _dfs_cfg(cfg, on_back_edge=on_back_edge)
    return loops


def is_cfg_reducible(cfg: List[List[int]]) -> bool:
    """Returns if the given CFG is reducible, i.e., if each back-edge in the
    CFG forms a natural loop."""
    is_reducible = True

    def on_back_edge(cfg, doms, preds, header, curr):
        nonlocal is_reducible
        if not is_reducible:
            return
        try:
            loop = _extract_loop(cfg, doms, preds, header, curr)
        except NotANaturalLoop:
            is_reducible = False

    _dfs_cfg(cfg, on_back_edge=on_back_edge)
    return is_reducible
