import unittest
from . import local_value_numbering as lvn


class LocalValueNumberingTest(unittest.TestCase):
    def test_lvn_works_without_multiple_assignments(self):
        """Test that the block:

            a: int = const 4;
            b: int = const 2;
            s1: int = add a b;
            s2: int = add a b;
            m: int = mul s1 s2;
        
        is trannsformed to:

            a__0: int = const 4;
            b__1: int = const 2;
            s1__2: int = add a__0 b__1;
            s2__3: int = id s1__2;
            m__4: int = mul s1__2 s1__2;
        """
        block = [{
            "dest": "a",
            "op": "const",
            "type": "int",
            "value": 4
        }, {
            "dest": "b",
            "op": "const",
            "type": "int",
            "value": 2
        }, {
            "args": ["a", "b"],
            "dest": "s1",
            "op": "add",
            "type": "int"
        }, {
            "args": ["a", "b"],
            "dest": "s2",
            "op": "add",
            "type": "int"
        }, {
            "args": ["s1", "s2"],
            "dest": "m",
            "op": "mul",
            "type": "int"
        }, {
            "args": ["m"],
            "op": "print"
        }]
        transformed_block = lvn.local_value_numbering_transform(block)
        from pprint import pprint
        pprint(transformed_block)
        self.assertEqual(transformed_block, [{
            "dest": "a__0",
            "op": "const",
            "type": "int",
            "value": 4
        }, {
            "dest": "b__1",
            "op": "const",
            "type": "int",
            "value": 2
        }, {
            "args": ["a__0", "b__1"],
            "dest": "s1__2",
            "op": "add",
            "type": "int"
        }, {
            "dest": "s2__3",
            "op": "id",
            "type": "int",
            "args": ["s1__2"],
        }, {
            "args": ["s1__2", "s1__2"],
            "dest": "m__4",
            "op": "mul",
            "type": "int"
        }, {
            "args": ["m__4"],
            "op": "print"
        }])

    def test_lvn_works_with_multiple_assignments(self):
        """Test that the block:

            a: int = const 4;
            b: int = const 2;
            x: int = add a b;
            x: int = const 10;
            y: int = add a b;
            print y;
        
        is transformed to:

            a__0: int = const 4;
            b__1: int = const 2;
            x__2: int = add a__0 b__1;
            x__3: int = const 10;
            y__4: int = id x__2;
            print y;
        """
        block = [{
            "dest": "a",
            "op": "const",
            "type": "int",
            "value": 4
        }, {
            "dest": "b",
            "op": "const",
            "type": "int",
            "value": 2
        }, {
            "args": ["a", "b"],
            "dest": "x",
            "op": "add",
            "type": "int"
        }, {
            "value": 10,
            "dest": "x",
            "op": "const",
            "type": "int"
        }, {
            "args": ["a", "b"],
            "dest": "y",
            "op": "add",
            "type": "int"
        }, {
            "args": ["y"],
            "op": "print"
        }]

        transformed_block = lvn.local_value_numbering_transform(block)
        from pprint import pprint
        pprint(transformed_block)
        self.assertEqual(transformed_block, [{
            "dest": "a__0",
            "op": "const",
            "type": "int",
            "value": 4
        }, {
            "dest": "b__1",
            "op": "const",
            "type": "int",
            "value": 2
        }, {
            "args": ["a__0", "b__1"],
            "dest": "x__2",
            "op": "add",
            "type": "int"
        }, {
            "value": 10,
            "dest": "x__3",
            "op": "const",
            "type": "int"
        }, {
            "args": ["x__2"],
            "dest": "y__4",
            "op": "id",
            "type": "int"
        }, {
            "args": ["y__4"],
            "op": "print"
        }])

    def test_lvn_works_with_multiple_assignments2(self):
        """Test that the block:

            a: int = const 4;
            b: int = const 2;
            x: int = add a b;
            y: int = id x;
            x: int = const 10;
            z: int = id x;
            s: int = add x y;
            print s;
        
        is transformed to:

            a__0: int = const 4;
            b__1: int = const 2;
            x__2: int = add a__0 b__1;
            y__3: int = id x__2;
            x__4: int = const 10;
            z__5: int = id x__4;
            s__6: int = add x__4 y__3;
            print s;
        """
        block = [{
            "dest": "a",
            "op": "const",
            "type": "int",
            "value": 4
        }, {
            "dest": "b",
            "op": "const",
            "type": "int",
            "value": 2
        }, {
            "args": ["a", "b"],
            "dest": "x",
            "op": "add",
            "type": "int"
        }, {
            "args": ["x"],
            "dest": "y",
            "op": "id",
            "type": "int"
        }, {
            "value": 10,
            "dest": "x",
            "op": "const",
            "type": "int"
        }, {
            "args": ["x"],
            "dest": "z",
            "op": "id",
            "type": "int"
        }, {
            "args": ["x", "y"],
            "dest": "s",
            "op": "add",
            "type": "int"
        }, {
            "args": ["s"],
            "op": "print"
        }]
        transformed_block = lvn.local_value_numbering_transform(block)
        from pprint import pprint
        pprint(transformed_block)
        self.assertEqual(transformed_block, [{
            "dest": "a__0",
            "op": "const",
            "type": "int",
            "value": 4
        }, {
            "dest": "b__1",
            "op": "const",
            "type": "int",
            "value": 2
        }, {
            "args": ["a__0", "b__1"],
            "dest": "x__2",
            "op": "add",
            "type": "int"
        }, {
            "args": ["x__2"],
            "dest": "y__3",
            "op": "id",
            "type": "int"
        }, {
            "value": 10,
            "dest": "x__4",
            "op": "const",
            "type": "int"
        }, {
            "args": ["x__4"],
            "dest": "z__5",
            "op": "id",
            "type": "int"
        }, {
            "args": ["x__4", "y__3"],
            "dest": "s__6",
            "op": "add",
            "type": "int"
        }, {
            "args": ["s__6"],
            "op": "print"
        }
        ])


if __name__ == '__main__':
    unittest.main()
