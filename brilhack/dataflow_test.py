import unittest
from pprint import pprint

from . import dataflow
from .basic_blocks import BBProgram


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
        bbprog = BBProgram({
            "functions": [{
                "args": [{
                    "name": "x",
                    "type": "int"
                }],
                "instrs": [{
                    "dest": "v",
                    "op": "const",
                    "type": "int",
                    "value": 0
                }, {
                    "dest": "incr",
                    "op": "const",
                    "type": "int",
                    "value": 1
                }, {
                    "label": "loop"
                }, {
                    "args": ["v", "x"],
                    "dest": "end",
                    "op": "eq",
                    "type": "bool"
                }, {
                    "args": ["end"],
                    "labels": ["end", "body"],
                    "op": "br"
                }, {
                    "label": "body"
                }, {
                    "args": ["v"],
                    "op": "print"
                }, {
                    "args": ["v", "incr"],
                    "dest": "v",
                    "op": "add",
                    "type": "int"
                }, {
                    "labels": ["loop"],
                    "op": "jmp"
                }, {
                    "label": "end"
                }],
                "name":
                "main"
            }]
        })
        defs = dataflow.reaching_defs(bbprog.funcs["main"])
        self.assertEqual(defs, [
            {
                "x": {None},
                "v": {(0, 0)},
                "incr": {(0, 1)}
            },
            {
                "x": {None},
                "v": {(0, 0), (2, 2)},
                "incr": {(0, 1)},
                "end": {(1, 1)}
            },
            {
                "x": {None},
                "v": {(2, 2)},
                "incr": {(0, 1)},
                "end": {(1, 1)}
            },
            {
                "x": {None},
                "v": {(0, 0), (2, 2)},
                "incr": {(0, 1)},
                "end": {(1, 1)}
            },
        ])

    def test_reaching_defs(self):
        bbprog = BBProgram({
            "functions": [{
                "instrs": [{
                    "dest": "v",
                    "op": "const",
                    "type": "int",
                    "value": 4
                }, {
                    "labels": ["somewhere"],
                    "op": "jmp"
                }, {
                    "dest": "v",
                    "op": "const",
                    "type": "int",
                    "value": 2
                }, {
                    "label": "somewhere"
                }, {
                    "args": ["v"],
                    "op": "print"
                }],
                "name":
                "main"
            }]
        })
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