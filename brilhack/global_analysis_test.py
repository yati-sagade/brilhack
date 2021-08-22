import unittest
from .basic_blocks import BBProgram
from .global_analysis import dominators, dominator_tree, extract_natural_loops
from .global_analysis import is_cfg_reducible, loop_invariant_code_motion
from . import parser
from pprint import pformat


class GlobalAnalysisTest(unittest.TestCase):
    def test_dominators(self):
        cfg = [[1], [5, 2], [3, 4], [4], [1], [6], []]
        self.assertEqual(dominators(cfg), [
            {0},
            {0, 1},
            {0, 1, 2},
            {0, 1, 2, 3},
            {0, 1, 2, 4},
            {0, 1, 5},
            {0, 1, 5, 6},
        ])

    def test_dominator_tree(self):
        cfg = [[1], [5, 2], [3, 4], [4], [1], [6], []]
        self.assertEqual(dominator_tree(cfg), [
            {1},
            {5, 2},
            {3, 4},
            set(),
            set(),
            {6},
            set(),
        ])

    def test_extract_natural_loops(self):
        self.assertEqual(
            extract_natural_loops(
                cfg=[[1], [5, 2], [3, 4], [4], [1], [6], []]),
            [(1, {1, 2, 3, 4})])

        # This CFG is not reducible, since the only loop it contains is not
        # a natural loop (node 3 forms a back-edge with header node 1, but
        # there is an external 2->3 edge that makes the loop not natural).
        self.assertEqual(extract_natural_loops(cfg=[[1, 2], [3], [3], [1]]),
                         [])

    def test_is_cfg_reducible(self):
        self.assertTrue(
            is_cfg_reducible(cfg=[[1], [5, 2], [3, 4], [4], [1], [6], []]))
        self.assertFalse(is_cfg_reducible(cfg=[[1, 2], [2], [1]]))
        self.assertFalse(is_cfg_reducible(cfg=[[1, 2], [3], [3], [1]]))

    def test_loop_invariant_code_motion1(self):
        bbprog = BBProgram(prog=parser.parse("""
          @main() {
            .start:
            i: int = const 0;
            j: int = const 1;
            limit: int = const 10;

            .loop:
            done: bool = eq i limit;
            br done .exit .iterate;

            .iterate:
            print i;
            incr: int = add j j;
            i: int = add i incr;

            jmp .loop;
            .exit:
          }
        """))
        original_blocks = [
            [
                {
                    'label': 'start'
                },
                {
                    'dest': 'i',
                    'op': 'const',
                    'type': 'int',
                    'value': 0
                },
                {
                    'dest': 'j',
                    'op': 'const',
                    'type': 'int',
                    'value': 1
                },
                {
                    'dest': 'limit',
                    'op': 'const',
                    'type': 'int',
                    'value': 10
                },
            ],
            [
                {
                    'label': 'loop'
                },
                {
                    'args': ['i', 'limit'],
                    'dest': 'done',
                    'op': 'eq',
                    'type': 'bool'
                },
                {
                    'args': ['done'],
                    'labels': ['exit', 'iterate'],
                    'op': 'br'
                },
            ],
            [
                {
                    'label': 'iterate'
                },
                {
                    'args': ['i'],
                    'op': 'print'
                },
                {
                    'args': ['j', 'j'],
                    'dest': 'incr',
                    'op': 'add',
                    'type': 'int'
                },
                {
                    'args': ['i', 'incr'],
                    'dest': 'i',
                    'op': 'add',
                    'type': 'int'
                },
                {
                    'labels': ['loop'],
                    'op': 'jmp'
                },
            ],
            [
                {
                    'label': 'exit'
                },
            ],
        ]

        expected_blocks = [
            [
                {
                    'label': 'start'
                },
                {
                    'dest': 'i',
                    'op': 'const',
                    'type': 'int',
                    'value': 0
                },
                {
                    'dest': 'j',
                    'op': 'const',
                    'type': 'int',
                    'value': 1
                },
                {
                    'dest': 'limit',
                    'op': 'const',
                    'type': 'int',
                    'value': 10
                },
            ],
            [
                {
                    'label': 'loop'
                },
                {
                    'args': ['i', 'limit'],
                    'dest': 'done',
                    'op': 'eq',
                    'type': 'bool'
                },
                {
                    'args': ['done'],
                    'labels': ['exit', 'iterate'],
                    'op': 'br'
                },
            ],
            [
                {
                    'label': 'iterate'
                },
                {
                    'args': ['i'],
                    'op': 'print'
                },
                {
                    'args': ['j', 'j'],
                    'dest': 'incr',
                    'op': 'add',
                    'type': 'int'
                },
                {
                    'args': ['i', 'incr'],
                    'dest': 'i',
                    'op': 'add',
                    'type': 'int'
                },
                {
                    'labels': ['__preheader_loop'],
                    'op': 'jmp'
                },
            ],
            [
                {
                    'label': 'exit'
                },
            ],
            [
                {
                    'label': '__preheader_loop'
                },
                {
                    'args': ['j', 'j'],
                    'dest': 'incr',
                    'op': 'add',
                    'type': 'int'
                },
                {
                    'op': 'jmp',
                    'labels': ['loop']
                },
            ],
        ]
        main = bbprog.funcs['main']
        optmain = loop_invariant_code_motion(main)
        self.assertEqual(main.blocks, original_blocks)
        self.assertEqual(optmain.blocks, expected_blocks)

    def test_loop_invariant_code_motion2(self):
        """Test that in the following program, the `incr: int add j j;` instr
        is NOT moved outside the loop, since there is a downstream use of the 
        variable that will otherwise be clobbered if the loop runs 0 times.

            @main(limit: int) {
              .start:
              i: int = const 0;
              j: int = const 1;
              incr: int = const 0;

              .loop:
              done: bool = eq i limit;
              br done .exit .iterate;

              .iterate:
              print i;
              incr: int = add j j;
              i: int = add i incr;

              jmp .loop;
              .exit:
              print incr;
            }
        """
        bbprog = BBProgram(prog=parser.parse("""
          @main(limit: int) {
            .start:
            i: int = const 0;
            j: int = const 1;
            incr: int = const 0;

            .loop:
            done: bool = eq i limit;
            br done .exit .iterate;

            .iterate:
            print i;
            incr: int = add j j;
            i: int = add i incr;

            jmp .loop;
            .exit:
            print incr;
          }
        """))
        original_blocks = [
            [
                {
                    'label': 'start'
                },
                {
                    'dest': 'i',
                    'op': 'const',
                    'type': 'int',
                    'value': 0
                },
                {
                    'dest': 'j',
                    'op': 'const',
                    'type': 'int',
                    'value': 1
                },
                {
                    'dest': 'incr',
                    'op': 'const',
                    'type': 'int',
                    'value': 0
                },
            ],
            [
                {
                    'label': 'loop'
                },
                {
                    'args': ['i', 'limit'],
                    'dest': 'done',
                    'op': 'eq',
                    'type': 'bool'
                },
                {
                    'args': ['done'],
                    'labels': ['exit', 'iterate'],
                    'op': 'br'
                },
            ],
            [
                {
                    'label': 'iterate'
                },
                {
                    'args': ['i'],
                    'op': 'print'
                },
                {
                    'args': ['j', 'j'],
                    'dest': 'incr',
                    'op': 'add',
                    'type': 'int'
                },
                {
                    'args': ['i', 'incr'],
                    'dest': 'i',
                    'op': 'add',
                    'type': 'int'
                },
                {
                    'labels': ['loop'],
                    'op': 'jmp'
                },
            ],
            [
                {
                    'label': 'exit'
                },
                {
                    'args': ['incr'],
                    'op': 'print'
                },
            ],
        ]
        main = bbprog.funcs['main']
        optmain = loop_invariant_code_motion(main)
        self.assertEqual(main.blocks, original_blocks)
        self.assertEqual(optmain.blocks, original_blocks)

    def test_loop_invariant_code_motion3(self):
        """Test that in the following program, the `incr: int add j j;` instr
        is moved outside the loop, although there is an existing def
        outside the loop that dominates the loop since,
          1. The def inside the loop also dominates all uses of incr inside the
          loop, AND,
          2. There is no use of the var after the loop, AND
          3. This operation (add) is safe to perform speculatively (i.e., cannot
          throw).

            @main(limit: int) {
              .start:
              i: int = const 0;
              j: int = const 1;
              incr: int = const 0;

              .loop:
              done: bool = eq i limit;
              br done .exit .iterate;

              .iterate:
              print i;
              incr: int = add j j;
              i: int = add i incr;

              jmp .loop;
              .exit:
            }
        """
        self.maxDiff = None
        bbprog = BBProgram(prog=parser.parse("""
          @main(limit: int) {
            .start:
            i: int = const 0;
            j: int = const 1;
            incr: int = const 0;

            .loop:
            done: bool = eq i limit;
            br done .exit .iterate;

            .iterate:
            print i;
            incr: int = add j j;
            i: int = add i incr;

            jmp .loop;
            .exit:
          }
        """))
        original_blocks = [
            [
                {
                    'label': 'start'
                },
                {
                    'dest': 'i',
                    'op': 'const',
                    'type': 'int',
                    'value': 0
                },
                {
                    'dest': 'j',
                    'op': 'const',
                    'type': 'int',
                    'value': 1
                },
                {
                    'dest': 'incr',
                    'op': 'const',
                    'type': 'int',
                    'value': 0
                },
            ],
            [
                {
                    'label': 'loop'
                },
                {
                    'args': ['i', 'limit'],
                    'dest': 'done',
                    'op': 'eq',
                    'type': 'bool'
                },
                {
                    'args': ['done'],
                    'labels': ['exit', 'iterate'],
                    'op': 'br'
                },
            ],
            [
                {
                    'label': 'iterate'
                },
                {
                    'args': ['i'],
                    'op': 'print'
                },
                {
                    'args': ['j', 'j'],
                    'dest': 'incr',
                    'op': 'add',
                    'type': 'int'
                },
                {
                    'args': ['i', 'incr'],
                    'dest': 'i',
                    'op': 'add',
                    'type': 'int'
                },
                {
                    'labels': ['loop'],
                    'op': 'jmp'
                },
            ],
            [
                {
                    'label': 'exit'
                },
            ],
        ]
        expected_blocks = [
            [
                {
                    'label': 'start'
                },
                {
                    'dest': 'i',
                    'op': 'const',
                    'type': 'int',
                    'value': 0
                },
                {
                    'dest': 'j',
                    'op': 'const',
                    'type': 'int',
                    'value': 1
                },
                {
                    'dest': 'incr',
                    'op': 'const',
                    'type': 'int',
                    'value': 0
                },
            ],
            [
                {
                    'label': 'loop'
                },
                {
                    'args': ['i', 'limit'],
                    'dest': 'done',
                    'op': 'eq',
                    'type': 'bool'
                },
                {
                    'args': ['done'],
                    'labels': ['exit', 'iterate'],
                    'op': 'br'
                },
            ],
            [
                {
                    'label': 'iterate'
                },
                {
                    'args': ['i'],
                    'op': 'print'
                },
                {
                    'args': ['j', 'j'],
                    'dest': 'incr',
                    'op': 'add',
                    'type': 'int'
                },
                {
                    'args': ['i', 'incr'],
                    'dest': 'i',
                    'op': 'add',
                    'type': 'int'
                },
                {
                    'labels': ['__preheader_loop'],
                    'op': 'jmp'
                },
            ],
            [
                {
                    'label': 'exit'
                },
            ],
            [
                {
                    'label': '__preheader_loop'
                },
                {
                    'args': ['j', 'j'],
                    'dest': 'incr',
                    'op': 'add',
                    'type': 'int'
                },
                {
                    'op': 'jmp',
                    'labels': ['loop']
                },
            ],
        ]
        main = bbprog.funcs['main']
        optmain = loop_invariant_code_motion(main)
        self.assertEqual(
            main.blocks, original_blocks,
            'Expected original blocks to not change. Got {}, expected {}'.
            format(main.blocks, original_blocks))
        self.assertEqual(
            optmain.blocks, expected_blocks,
            'After optimization, got ===\n{}\n===\nbut expected\n===\n{}\===\n'
            .format(pformat(optmain.blocks), pformat(expected_blocks)))

    def test_loop_invariant_code_motion4(self):
        """Unsafe instrs should never be hoisted.

          In the following program, `incr: int = div j limit;` is invariant wrt
          the loop, but hoisting it outside introduces a possibility of an
          exception which affects the semantics of the program. Such hoisting
          should never be done, so we expect no optimization for the following.

            @main(limit: int) {
              .start:
              i: int = const 0;
              j: int = const 1;
              incr: int = const 0;

              .loop:
              done: bool = eq i limit;
              br done .exit .iterate;

              .iterate:
              print i;
              incr: int = div j limit;
              i: int = add i incr;

              jmp .loop;
              .exit:
            }
        """
        bbprog = BBProgram(prog=parser.parse("""
          @main(limit: int) {
            .start:
            i: int = const 0;
            j: int = const 1;
            incr: int = const 0;

            .loop:
            done: bool = eq i limit;
            br done .exit .iterate;

            .iterate:
            print i;
            incr: int = div j limit;
            i: int = add i incr;

            jmp .loop;
            .exit:
          }
        """))
        original_blocks = [
            [
                {
                    'label': 'start'
                },
                {
                    'dest': 'i',
                    'op': 'const',
                    'type': 'int',
                    'value': 0
                },
                {
                    'dest': 'j',
                    'op': 'const',
                    'type': 'int',
                    'value': 1
                },
                {
                    'dest': 'incr',
                    'op': 'const',
                    'type': 'int',
                    'value': 0
                },
            ],
            [
                {
                    'label': 'loop'
                },
                {
                    'args': ['i', 'limit'],
                    'dest': 'done',
                    'op': 'eq',
                    'type': 'bool'
                },
                {
                    'args': ['done'],
                    'labels': ['exit', 'iterate'],
                    'op': 'br'
                },
            ],
            [
                {
                    'label': 'iterate'
                },
                {
                    'args': ['i'],
                    'op': 'print'
                },
                {
                    'args': ['j', 'limit'],
                    'dest': 'incr',
                    'op': 'div',
                    'type': 'int'
                },
                {
                    'args': ['i', 'incr'],
                    'dest': 'i',
                    'op': 'add',
                    'type': 'int'
                },
                {
                    'labels': ['loop'],
                    'op': 'jmp'
                },
            ],
            [
                {
                    'label': 'exit'
                },
            ],
        ]
        main = bbprog.funcs['main']
        optmain = loop_invariant_code_motion(main)
        self.assertEqual(main.blocks, original_blocks)
        self.assertEqual(optmain.blocks, original_blocks)
