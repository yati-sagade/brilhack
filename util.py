def is_value_op(instr):
    return 'dest' in instr


def is_effect_op(instr):
    return not is_value_op()


def is_terminator(instr):
    return instr.get('op') in ('jmp', 'br')


def is_label(instr):
    return 'label' in instr


def mklabel(label_name):
    return {"label": label_name}