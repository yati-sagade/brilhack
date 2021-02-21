from .basic_blocks import Function
from .util import is_value_op
import logging


def solve(func: Function, init, transfer_fn, merge_fn):
    num_blocks = len(func.blocks)

    # Map from block to predecessor index list.
    preds = [[] for _ in range(num_blocks)]
    for block, succs in enumerate(func.block_exits):
        for succ in succs:
            if succ < num_blocks:
                preds[succ].append(block)

    worklist = set(range(len(func.blocks)))
    invals = [init for _ in range(num_blocks)]
    outvals = [init for _ in range(num_blocks)]
    while worklist:
        block_idx = worklist.pop()
        block = func.blocks[block_idx]

        # The input to the transfer func for a block is the merger of
        # its current input value and output values of all predecessor
        # blocks.
        predvals = [outvals[p] for p in preds[block_idx]]
        predvals.append(invals[block_idx])

        invals[block_idx] = merge_fn(predvals)
        block_out = transfer_fn(func, block_idx, invals[block_idx])
        if block_out != outvals[block_idx]:
            outvals[block_idx] = block_out
            for succ_idx in func.block_exits[block_idx]:
                if succ_idx < num_blocks:
                    worklist.add(succ_idx)

    return outvals


# Definitions are maintained as a map {varname: (block_id, instr_id)}
# For function params, the value is None.
def reaching_defs_init(func: Function):
    return {a["name"]: {None} for a in func.args}


def reaching_defs_transfer(func, block_id, inval):
    block = func.blocks[block_id]
    outval = inval.copy()
    for i, instr in enumerate(block):
        if is_value_op(instr):
            v = instr['dest']
            if v in outval:
                logging.debug(
                    'Previous definition of {} from {} killed at {}'.format(
                        v, outval[v], (block_id, i)))
            outval[v] = {(block_id, i)}
    return outval


def reaching_defs_merge(vals):
    merged = {}
    for val in vals:
        for var, defs in val.items():
            s = merged.setdefault(var, set())
            for d in defs:
                s.add(d)
    return merged


def reaching_defs(func):
    return solve(func, reaching_defs_init(func), reaching_defs_transfer,
                 reaching_defs_merge)
