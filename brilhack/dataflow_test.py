import unittest
from pprint import pprint

from . import dataflow
from .basic_blocks import BBProgram
from . import parser


class DataFlowTest(unittest.TestCase):
    def test_reaching_defs_loop(self):
        """Test dataflow on the following program with a simple loop that prints
      0 through a given number (minus 1):

        @main(x: int) {
          v: int = const 0;
          incr: int = const 1;
          .loop:
          end: bool = eq v x;
          br end .end .body;
          .body:
          print v;
          v: int = add v incr;
          jmp .loop;
          .end:
        }
        """
        bbprog = BBProgram(prog=parser.parse("""
          @main(x: int) {
            v: int = const 0;
            incr: int = const 1;
            .loop:
            end: bool = eq v x;
            br end .end .body;
            .body:
            print v;
            v: int = add v incr;
            jmp .loop;
            .end:
          }"""))
        defs = dataflow.reaching_defs(bbprog.funcs["main"])
        self.assertEqual(defs, [
            {
                "x": {(None, 0)},
                "v": {(0, 0)},
                "incr": {(0, 1)}
            },
            {
                "x": {(None, 0)},
                "v": {(0, 0), (2, 2)},
                "incr": {(0, 1)},
                "end": {(1, 1)}
            },
            {
                "x": {(None, 0)},
                "v": {(2, 2)},
                "incr": {(0, 1)},
                "end": {(1, 1)}
            },
            {
                "x": {(None, 0)},
                "v": {(0, 0), (2, 2)},
                "incr": {(0, 1)},
                "end": {(1, 1)}
            },
        ])

    def test_reaching_defs(self):
        bbprog = BBProgram(prog=parser.parse("""
          @main() {
            v: int = const 4;
            jmp .somewhere;
            v: int = const 2;
            .somewhere:
            print v;
          }"""))
        defs = dataflow.reaching_defs(bbprog.funcs["main"])
        # defs[k] is the reaching defs at the end of the k^th block.
        # defs[k] is a dict mapping variable names to the set of
        # (block_id, instr_id) pairs of defs that reach the end of the k^th
        # block.
        self.assertEqual(
            defs,
            [
                {
                    "v": set([(0, 0)])
                },
                {
                    "v": set([(1, 0)])
                },
                {
                    # Both defs reach the end of the last block.
                    "v": set([(0, 0), (1, 0)])
                }
            ])


if __name__ == '__main__':
    unittest.main()