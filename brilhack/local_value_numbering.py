# LVN is a technique that enables many kinds of optimizations, including
# dead-code elimination, copy propagation, common-subexpression elimination,
# constant folding, etc. The "local" in LVN is because it operates at a
# basic-block level (as opposed to global value numbering, which transforms
# entire functions).
#
# This file contains the basic framework of LVN for
# bril, and can be tweaked in different ways to get all of the above
# optimizations. Usually the tweaks are in form of introducing some semantic
# awareness of the target language.
from . import util


def value_key(env, instr):
    if instr['op'] == 'const':
        # TODO(yati): Take types into account?
        return ('const', instr['value'])
    key = [instr['op']]
    for arg in instr['args']:
        key.append(env[arg])  # Crash ok if arg is not seen before.
    return tuple(key)


def reconstruct_instr(valtable, key, dest, instr):
    reconstructed = instr.copy()
    op = key[0]
    if op == 'const':
        reconstructed.update({'value': key[1], 'dest': dest})
    else:
        # Assume key ~ (op, arg1_valnum, arg2_valnum, ...)
        reconstructed.update({
            'op': op,
            'dest': dest,
            # List of canonical varnames for the argument valuetable indices.
            'args': [valtable[k][1] for k in key[1:]],
        })
    return reconstructed


def id_op(valtable, valnum, dest, typ):
    canonical_var = valtable[valnum][1]
    return {'op': 'id', 'dest': dest, 'args': [canonical_var], 'type': typ}

def rename_vars(basic_block):
    # Map from original var name to its currently active rename.
    curr = {}
    for idx, instr in enumerate(basic_block):
        if util.is_value_op(instr):
            dest = instr['dest']
            instr['dest'] = curr[dest] = '{}__{}'.format(instr['dest'], idx)
        if 'args' in instr:
            instr['args'] = [curr.get(arg, arg) for arg in instr['args']]


def local_value_numbering_transform(basic_block):
    # Each entry valtable[k] is a tuple
    #   (value_key, canonical_var)
    # which says that the k^th cached value has a key `value_key`, and was first
    # bound to the variable named by `canonical_var`.
    # The `value_key` tuple can refer to other entries in this table by index.
    valtable = []

    # Map from variable name to the index of value it holds in valtable.
    env = {}

    # Map from a value key to its index into valtable.
    valindex = {}

    rename_vars(basic_block)

    transformed_bb = []
    for idx, instr in enumerate(basic_block):
        key = value_key(env, instr)
        if key in valindex:
            num = valindex[key]
            # Because of the next block in this if ladder, we can never have
            # effect ops cached in valtable, so it is safe to assume we are
            # dealing with a value-op.
            env[instr['dest']] = num
            new_instr = id_op(valtable, num, instr['dest'], instr['type'])
        elif util.is_value_op(instr):
            num = len(valtable)
            dest = instr['dest']
            valtable.append((key, dest))
            valindex[key] = num
            env[dest] = num
            new_instr = reconstruct_instr(valtable, key, dest, instr)
        else:
            new_instr = instr
        transformed_bb.append(new_instr)
    return transformed_bb
