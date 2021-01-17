# There are two varieties of simple DCE to be performed:
# 1. Find value ops whose destinations are not used in effect operations and
#    delete them. This can be done globally (function level).
# 2. Find redundant variable assignments within a block and delete them. This
#    cannot be done as easily globally because of missing runtime control flow
#    information.
import logging
import basic_blocks
from util import is_value_op


def _global_dce(func: basic_blocks.Function) -> basic_blocks.Function:
    optfunc = basic_blocks.Function.filter_copy(func)

    # Perform multiple rounds of removal until there is no removal possible.
    while True:
        candidates = {}

        # Set of variable names that are used in the RHS of any op. Once seen
        # as used, this var may not be candidate for removal in this round.
        used = set()
        for block_idx, block in enumerate(optfunc.blocks):
            for instr_idx, instr in enumerate(block):
                for arg in instr.get('args', []):
                    used.add(arg)
                    candidates.pop(arg, None)
                if is_value_op(instr) and instr['dest'] not in used:
                    candidates[instr['dest']] = (block_idx, instr_idx)
        if not candidates:
            # This means there were no more opportunities, i.e., the optimization
            # has converged.
            return optfunc
        logging.debug('global dce: removing {} from function {}'.format(
            candidates, optfunc.name))
        optfunc = basic_blocks.Function.filter_copy(optfunc,
                                                    exclude=set(
                                                        candidates.values()))


def _local_dce(block):
    optblock = block[:]
    while True:
        remove = set()
        candidates = {}
        for idx, instr in enumerate(optblock):
            for arg in instr.get('args', []):
                candidates.pop(arg, None)
            if is_value_op(instr):
                dst = instr['dest']
                # The previous assignment of this dst has been unused, and we
                # are at another assignment. Hence the existing assignment can
                # be removed.
                if dst in candidates:
                    remove.add(candidates[dst])
                candidates[dst] = idx
        if not remove:
            return optblock
        remove_vars = [block[idx] for idx in sorted(remove)]
        logging.debug('local dce: removing {} from block {}'.format(
            remove_vars, idx))
        optblock = [b for i, b in enumerate(optblock) if i not in remove]
    return optblock


def _process_func(func: basic_blocks.Function) -> basic_blocks.Function:
    optfunc = _global_dce(func)
    for i in range(len(optfunc.blocks)):
        optfunc.blocks[i] = _local_dce(optfunc.blocks[i])
    return optfunc


def dead_code_elimination(
        bbprog: basic_blocks.BBProgram) -> basic_blocks.BBProgram:
    optprog = basic_blocks.BBProgram()
    for name, func in bbprog.funcs.items():
        optprog.funcs[name] = _process_func(func)
    return optprog


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    import json, sys
    prog = json.load(sys.stdin)
    bbprog = basic_blocks.BBProgram(prog)
    optprog = dead_code_elimination(bbprog)
    json.dump(optprog.bril_dict(), sys.stdout)
