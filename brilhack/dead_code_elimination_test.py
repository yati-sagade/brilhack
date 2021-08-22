import unittest
from .basic_blocks import BBProgram
from . import dead_code_elimination as dce
from . import parser


class DeadCodeEliminationTest(unittest.TestCase):
    def test_local_and_global_dce(self):
        """Test that the following program:

            @main {
              a: int = const 1;
              a: int = const 2;
              b: int = const 3;
              a: int = add a a;
              b: int = id a;
              print b;
            }

        is optimized to:

            @main {
              a: int = const 2;
              a: int = add a a;
              print b;
            }
        """
        bbprog = BBProgram(prog=parser.parse("""
          @main {
              a: int = const 1;
              a: int = const 2;
              b: int = const 3;
              a: int = add a a;
              b: int = id a;
              print b;
          }"""))
        optprog = dce.dead_code_elimination(bbprog)
        self.assertEqual(optprog.funcs['main'].blocks, [
            [{
                "dest": "a",
                "op": "const",
                "type": "int",
                "value": 2
            }, {
                "args": ["a", "a"],
                "dest": "a",
                "op": "add",
                "type": "int"
            }, {
                "dest": "b",
                "op": "id",
                "args": ["a"],
                "type": "int",
            }, {
                "args": ["b"],
                "op": "print"
            }],
        ])

    def test_global_dce_preserves_transitively_used_vars(self):
        """Test that the following program:

            @main {
              a: int = const 1;
              b: int = const 2;
              c: int = const 3;
              d: int = id c;
              print d;
            }

        is optimized to:

            @main {
              c: int = const 3;
              d: int = id c;
              print d;
            }
        """
        bbprog = BBProgram(prog=parser.parse("""
          @main {
            a: int = const 1;
            b: int = const 2;
            c: int = const 3;
            d: int = id c;
            print d;
          }"""))
        optprog = dce.dead_code_elimination(bbprog)
        self.assertEqual(optprog.funcs['main'].blocks, [
            [{
                "dest": "c",
                "op": "const",
                "type": "int",
                "value": 3
            }, {
                "args": ["c"],
                "dest": "d",
                "op": "id",
                "type": "int"
            }, {
                "args": ["d"],
                "op": "print"
            }],
        ])

    def test_global_dce_removes_unused_vars(self):
        """Test that the following program:

            @main {
              a: int = const 1;
              b: int = const 2;
              c: int = const 3;
              d: int = const 4;
              print d;
            }
         
         is optimized to:

            @main {
              d: int = const 4;
              print d;
            }
        """
        bbprog = BBProgram(prog=parser.parse("""
          @main {
            a: int = const 1;
            b: int = const 2;
            c: int = const 3;
            d: int = const 4;
            print d;
          }"""))
        optprog = dce.dead_code_elimination(bbprog)
        self.assertEqual(optprog.funcs['main'].blocks, [
            [{
                "dest": "d",
                "op": "const",
                "type": "int",
                "value": 4
            }, {
                "args": ["d"],
                "op": "print"
            }],
        ])


if __name__ == '__main__':
    unittest.main()
