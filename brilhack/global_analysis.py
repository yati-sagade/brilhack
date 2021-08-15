from typing import List, Set, Dict, Tuple
from functools import reduce
import logging
from collections import deque

from .basic_blocks import Function
from .util import is_value_op, mklabel, mkjmp, is_terminator
from .dataflow import ReachingDefsMap, reaching_defs


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


def extract_natural_loops(cfg: List[List[int]]) -> List[Set[int]]:
    """Returns all natural loops in `cfg`."""
    loops = []

    def on_back_edge(cfg, doms, preds, header, curr):
        try:
            loop = _extract_loop(cfg, doms, preds, header, curr)
            loops.append((header, loop))
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


def _get_reaching_def_blocks(block_reaching_defs: Dict[str, Set[Tuple[int,
                                                                      int]]],
                             varname: str) -> Set[int]:
    return {block_id for block_id, _ in block_reaching_defs[varname]}


def _find_invariant_instrs(func: Function, loop: Set[int],
                           reaching_defs: ReachingDefsMap,
                           dominators: List[Set[int]]):
    """Returns a list of (block_idx, instr_idx) pairs that point to instructions
    inside the given natural `loop` that are invariant w.r.t. that loop, and are
    safe to move outside.

    Args:
      func: Function containing the given loop.
      loop: Loop, as a set of block ids constituting the loop, to find LI
      instructions in.
      reaching_defs: All reaching definitions at the end of each block in
      `func`.
      dominators: dominators[block_id] = set of block ids that dominate
      block_id.
    
    """
    li_instrs = set()

    # var_uses[(block_id, instr_id, varname)] = set of blocks that use varname
    # defined at block_id, instr_id.
    var_uses = dict()
    changed = True
    while changed:
        changed = False
        for block_id in loop:
            block = func.blocks[block_id]
            for instr_id, instr in enumerate(block):
                if not is_value_op(instr):
                    continue

                if (block_id, instr_id) in li_instrs:
                    continue

                # For instr to be LI, for each arg, each reaching def of this
                # arg must be either:
                # - From outside the loop, OR
                # - Itself LI.
                is_loop_invariant = True
                for argname in instr['args']:
                    arg_reaching_defs = reaching_defs[block_id][argname]
                    in_loop_reaching_defs = {
                        (block_id, instr_id)
                        for block_id, instr_id in arg_reaching_defs
                        if block_id in loop
                    }
                    for def_block_id, def_instr_id in in_loop_reaching_defs:
                        var_uses.setdefault(
                            (def_block_id, def_instr_id, argname),
                            set()).add(block_id)

                    if in_loop_reaching_defs and not li_instrs.issuperset(
                            in_loop_reaching_defs):
                        logging.debug(
                            'Instr {} ({}) NOT LI because all the reaching defs from inside the lop are not LI: {}'
                            .format((block_id, instr_id), instr,
                                    in_loop_reaching_defs))
                        is_loop_invariant = False

                if is_loop_invariant:
                    logging.debug('Marking instruction {} ({}) as LI'.format(
                        (block_id, instr_id), instr))
                    li_instrs.add((block_id, instr_id))
                    changed = True
    logging.debug('Loop invariant code motion candidates: {}'.format([
        (b, i, func.blocks[b][i]) for b, i in li_instrs
    ]))

    # For an LI instruction to be safe for motion,
    # - It must dominate all uses in the loop, AND,
    # - It must be the only definition for that var in the loop, AND,
    # - The var must be dead in all blocks after the loop exit.
    movable_instrs = set()
    for block_id, instr_id in li_instrs:
        varname = func.blocks[block_id][instr_id]['dest']
        if not var_uses.get((block_id, instr_id, varname)):
            continue

        is_movable = True
        for using_block_id in var_uses[block_id, instr_id, varname]:
            if block_id not in dominators[using_block_id]:
                logging.debug(
                    'For LI instr {}, the block does not dominate a '
                    'use in block {} of the loop, should skip!'.format(
                        (block_id, instr_id), using_block_id))
                is_movable = False
                break

        if is_movable:
            # TODO(yati): Need to also check if the L.I. definition is dead
            # after the loop, else moving it before the loop will cause
            # incorrect behaviour!!.
            movable_instrs.add((block_id, instr_id))

    return movable_instrs


def _add_preheader_block(func: Function, instrs: List[Dict], header_id: int,
                         header_label: str):
    for block_id, exits in enumerate(func.block_exits):
        for i, exit in enumerate(exits):
            if exit == len(func.blocks):
                exits[i] += 1
    preheader_label = '__preheader_{}'.format(header_label)
    preheader = [mklabel(preheader_label)]
    for instr in instrs:
        preheader.append(instr)
    preheader.append(mkjmp(header_label))
    preheader_id = len(func.blocks)
    for block_id, block in enumerate(func.blocks):
        if not block:
            continue
        instr = block[-1]
        if is_terminator(instr) and instr['op'] in ('jmp', 'br'):
            instr['labels'] = [
                preheader_label if label == header_label else label
                for label in instr['labels']
            ]
            func.block_exits[block_id] = [
                preheader_id if target == header_id else target
                for target in func.block_exits[block_id]
            ]
    func.blocks.append(preheader)
    func.block_exits.append([header_id])


def loop_invariant_code_motion(func: Function) -> Function:
    func = func.copy()
    doms = dominators(func.block_exits)
    defs = reaching_defs(func)
    li = []
    inv_label_index = {
        block_id: label
        for label, block_id in func.label_index.items()
    }
    for header_id, loop in extract_natural_loops(func.block_exits):
        logging.debug('[LICM] Processing loop {}'.format(loop))
        instr_ids = _find_invariant_instrs(func, loop, defs, doms)
        if not instr_ids:
            continue
        instrs = [
            func.blocks[block_id][instr_id]
            for block_id, instr_id in sorted(instr_ids)
        ]
        header_label = inv_label_index[header_id]
        if instrs:
            _add_preheader_block(func, instrs, header_id, header_label)
    return func
