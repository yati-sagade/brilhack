def is_value_op(instr):
    return 'dest' in instr


def is_effect_op(instr):
    return not is_value_op(instr)


def is_terminator(instr):
    return instr.get('op') in ('jmp', 'br')


def is_label(instr):
    return 'label' in instr


def mklabel(label_name):
    return {"label": label_name}


def mkjmp(target):
    return {"op": "jmp", "labels": [target]}


def can_have_side_effects(instr):
    """Returns if instr is an effect op OR if it can throw exceptions."""
    return is_effect_op(instr) or instr['op'] in ('div', )


def instr_as_string(instr):
    if 'label' in instr:
        return '.{}:'.format(instr['label'])
    if is_value_op(instr):
        if instr['op'] == 'const':
            return '{}: {} = const {}'.format(instr['dest'], instr['type'],
                                              instr['value'])
        return '{}: {} = {} {}'.format(instr['dest'], instr['type'],
                                       instr['op'], ' '.join(instr['args']))
    if is_effect_op(instr):
        if instr['op'] == 'jmp':
            return 'jmp .{}'.format(instr['labels'][0])
        if instr['op'] == 'br':
            return 'br {} .{} .{}'.format(instr['args'][0], instr['labels'][0],
                                          instr['labels'][1])
