from .basic_blocks import Function, BBProgram
from .util import is_value_op
from typing import Dict, List, Tuple
import logging
import argparse
import json
import sys

ALL_ANALYSES = {}


def analysis(name):
    def decorator(func):
        ALL_ANALYSES[name] = func
        return func

    return decorator


class DataFlowAnalysis:
    def initval(self):
        raise NotImplementedError("Impls must override initval().")

    def transfer(self, func, block_id, inval):
        raise NotImplementedError("Impls must override transfer().")

    def merge(self, vals):
        raise NotImplementedError("Impls must override merge().")

    def solve(self, func: Function):
        """Solve a dataflow problem with the worklist algorithm."""
        num_blocks = len(func.blocks)

        # Map from block to predecessor index list.
        preds = [[] for _ in range(num_blocks)]
        for block, succs in enumerate(func.block_exits):
            for succ in succs:
                if succ < num_blocks:
                    preds[succ].append(block)

        worklist = set(range(len(func.blocks)))
        invals = [self.initval(func) for _ in range(num_blocks)]
        outvals = [self.initval(func) for _ in range(num_blocks)]
        while worklist:
            block_idx = worklist.pop()
            block = func.blocks[block_idx]

            # The input to the transfer func for a block is the merger of
            # its current input value and output values of all predecessor
            # blocks.
            predvals = [outvals[p] for p in preds[block_idx]]
            predvals.append(invals[block_idx])

            invals[block_idx] = self.merge(predvals)
            block_out = self.transfer(func, block_idx, invals[block_idx])
            if block_out != outvals[block_idx]:
                outvals[block_idx] = block_out
                for succ_idx in func.block_exits[block_idx]:
                    if succ_idx < num_blocks:
                        worklist.add(succ_idx)

        return outvals


# Map from variable name to the set of (block_id, instr_id) of instructions
# that define it. There can be multiple reaching definitions of the same var
# at a given point in the program due to, e.g., conditional jumps in a CFG.
ReachingDefsMap = dict[str, set[tuple[int, int]]]


class ReachingDefinitions(DataFlowAnalysis):
    def initval(self, func: Function) -> ReachingDefsMap:
        # Definitions are maintained as a map {varname: (block_id, instr_id)}
        # For function params, the value is (None, param_index), where param_index is
        # the 0-based index of the param.
        return {a["name"]: {(None, i)} for i, a in enumerate(func.args)}

    def transfer(self, func, block_id, inval) -> ReachingDefsMap:
        block = func.blocks[block_id]
        outval = inval.copy()
        for i, instr in enumerate(block):
            if is_value_op(instr):
                v = instr['dest']
                if v in outval:
                    logging.debug(
                        'Previous definition of {} from {} killed at {}'.
                        format(v, outval[v], (block_id, i)))
                outval[v] = {(block_id, i)}
        return outval

    def merge(self, vals) -> ReachingDefsMap:
        merged = {}
        for val in vals:
            for var, defs in val.items():
                s = merged.setdefault(var, set())
                for d in defs:
                    s.add(d)
        return merged


@analysis("reaching_defs")
def reaching_defs(func) -> list[ReachingDefsMap]:
    """Returns the map of reaching variable defs at the end of each block."""
    return ReachingDefinitions().solve(func)


def main(args):
    afunc = ALL_ANALYSES[args.analysis]
    if args.input is None:
        prog = json.load(sys.stdin)
        bbprog = BBProgram(prog)
        for name, func in bbprog.funcs.items():
            result = afunc(func)
            print('Function {}\n----------\n{}\n'.format(result))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Run data flow analyses on bril programs')
    parser.add_argument(
        '--input',
        help="Input bril (JSON) program file. If not given, read from STDIN.")
    parser.add_argument('--analysis',
                        help="Name of the analysis to run, one of: {}".format(
                            ", ".join(sorted(ALL_ANALYSES.keys()))))
    args = parser.parse_args()
    main(args)
