from util import is_terminator, is_label


def _make_blocks(instrs):
    blocks = []
    label_index = {}

    curr_block = []
    for instr in instrs:
        if not is_label(instr):
            curr_block.append(instr)

        if is_label(instr) or is_terminator(instr):
            blocks.append(curr_block)
            curr_block = []
            if is_label(instr):
                label_index[instr['label']] = len(blocks)

    if curr_block:
        blocks.append(curr_block)

    return blocks, label_index


def _build_cfg(blocks, label_index):
    cfg = []
    for i, block in enumerate(blocks):
        last = block[-1]
        if is_terminator(last):
            next_blocks = [label_index[label] for label in last['labels']]
        else:
            next_blocks = [i + 1]
        cfg.append(next_blocks)
    return cfg


class Function:
    def __init__(self):
        self.blocks = []
        self.label_index = {}

        # Control flow information.
        # Map from block index to a list of block indices where control can
        # reach from it.
        self.block_exits = []

    @classmethod
    def from_instrs(cls, instrs):
        f = cls()
        f.blocks, f.label_index = _make_blocks(instrs)
        f.block_exits = _build_cfg(f.blocks, f.label_index)
        return f

    @classmethod
    def filter_copy(cls, other, exclude=None):
        """`exclude` is a set of (block_idx, instr_idx) pairs which are
        excluded from the copy."""
        f = cls()
        f.label_index = other.label_index.copy()
        f.block_exits = other.block_exits[:]
        for block_idx, block in enumerate(other.blocks):
            b = []
            for instr_idx, instr in enumerate(block):
                if not (exclude and (block_idx, instr_idx) in exclude):
                    b.append(instr)
            f.blocks.append(b)
        return f


class BBProgram:
    def __init__(self, prog=None):
        # Map from function to list of basic blocks in it.
        self.funcs = {}
        if prog is not None:
            for func in prog['functions']:
                self.funcs[func['name']] = Function.from_instrs(func['instrs'])
