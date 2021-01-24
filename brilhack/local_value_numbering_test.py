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

            a: int = const 4;
            b: int = const 2;
            s1: int = add a b;
            s2: int = id s2;
            m: int = mul s1 s1;
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
            "dest": "s2",
            "op": "id",
            "type": "int",
            "args": ["s1"],
        }, {
            "args": ["s1", "s1"],
            "dest": "m",
            "op": "mul",
            "type": "int"
        }, {
            "args": ["m"],
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

            a: int = const 4;
            b: int = const 2;
            x__2: int = add a b;
            x: int = const 10;
            y: int = id x__2;
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
            "dest": "x__2",
            "op": "add",
            "type": "int"
        }, {
            "value": 10,
            "dest": "x",
            "op": "const",
            "type": "int"
        }, {
            "args": ["x__2"],
            "dest": "y",
            "op": "id",
            "type": "int"
        }, {
            "args": ["y"],
            "op": "print"
        }])


if __name__ == '__main__':
    unittest.main()
