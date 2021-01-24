import unittest
from .basic_blocks import BBProgram


class BBProgramTest(unittest.TestCase):
    def test_bbprogram(self):
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
        self.assertEqual(len(bbprog.funcs), 1)
        self.assertIn('main', bbprog.funcs)

        main_func = bbprog.funcs['main']
        self.assertEqual(main_func.label_index, {"somewhere": 2})
        self.assertEqual(main_func.blocks, [[{
            "dest": "v",
            "op": "const",
            "type": "int",
            "value": 4
        }, {
            "labels": ["somewhere"],
            "op": "jmp"
        }], [{
            "dest": "v",
            "op": "const",
            "type": "int",
            "value": 2
        }], [{
            "label": "somewhere"
        }, {
            "args": ["v"],
            "op": "print"
        }]])

        # Verify CFG is built correctly.
        # Block 0 jmps to .somewhere (block 2)
        # Block 1 continues to block 2
        # Block 2 is the last block, so the next block "index" is 3.
        self.assertEqual(main_func.block_exits, [[2], [2], [3]])


if __name__ == '__main__':
    unittest.main()
