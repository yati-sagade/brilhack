"""Bril parser

This "parser" simply shells out to bril2json and then unmarshals the json as Python data.

Needs bril2json installed and on PATH, see https://github.com/sampsyo/bril.
"""
import sys
import json
import subprocess


def parse(bril_code: str):
    bril2json = subprocess.Popen(["bril2json"],
                                 stdin=subprocess.PIPE,
                                 stdout=subprocess.PIPE,
                                 stderr=subprocess.PIPE,
                                 text=True)
    stdout, stderr = bril2json.communicate(bril_code)
    if bril2json.returncode != 0:
        raise Exception(
            "Error parsing bril code with bril2json! Dumping output streams." +
            "=== stdout ===\n{}\n".format(stdout) +
            "=== stderr ===\n{}\n".format(stderr))
    return json.loads(stdout)


if __name__ == '__main__':
    parse(sys.stdin.read())
