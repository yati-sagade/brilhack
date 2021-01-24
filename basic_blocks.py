from .util import is_terminator, is_label, mklabel


def _make_blocks(instrs):
    blocks = []
    label_index = {}

    curr_block = []
    for instr in instrs:
        if not is_label(instr):
            curr_block.append(instr)

        if is_label(instr) or is_terminator(instr):
            if curr_block:
                blocks.append(curr_block)
                curr_block = []
            if is_label(instr):
                label_index[instr['label']] = len(blocks)

                # Technically we don't need the label here, but keeping it
                # makes generating bril again slightly easier.
                curr_block.append(instr)

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
    def __init__(self,
                 name,
                 args,
                 instrs=None,
                 blocks=None,
                 label_index=None,
                 block_exits=None):
        self.name = name

        assert (instrs is None) ^ (blocks is None and label_index is None),\
            "Either instrs, or (blocks and label_index and block_exits) must be given"
        if instrs is not None:
            self.blocks, self.label_index = _make_blocks(instrs)
        else:
            self.blocks = blocks
            self.label_index = label_index
        self.args = args

        # Control flow information.
        # Map from block index to a list of block indices where control can
        # reach from it.
        self.block_exits = _build_cfg(self.blocks, self.label_index)

    def to_bril(self):
        return {
            'name': self.name,
            'args': self.args,
            'instrs': [instr for block in self.blocks for instr in block]
        }

    @classmethod
    def filter_copy(cls, other, exclude=None):
        """`exclude` is a set of (block_idx, instr_idx) pairs which are
        excluded from the copy."""
        f = cls(name=other.name,
                args=other.args,
                blocks=[],
                label_index=other.label_index.copy(),
                block_exits=other.block_exits)
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
                print(func)
                self.funcs[func['name']] = Function(name=func['name'],
                                                    args=func.get('args', []),
                                                    instrs=func['instrs'])

    def bril_dict(self):
        return {'functions': [func.to_bril() for func in self.funcs.values()]}
