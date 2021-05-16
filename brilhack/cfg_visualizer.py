"""
Example usage (run from ../):

  $ bril2json <program.bril |python -mbrilhack.cfg_visualizer |dot -Tpng >program.cfg.png

"""
import sys
import json
import graphviz

from .basic_blocks import BBProgram, Function

def mkdot(prog: BBProgram):
  """Returns DOT source code for CFGs of all funcs in prog."""

  dot = graphviz.Digraph()
  for func in prog.funcs.values():
    invlabels = {blockid: label for label, blockid in func.label_index.items()}

    def _lab(blockid):
      return '{}/{}'.format(func.name, invlabels.get(blockid,
        '__block_{}'.format(blockid)))

    nblock = len(func.blocks)

    with dot.subgraph(name=func.name) as g:
      for blockid in range(nblock):
        g.node(_lab(blockid))
      for blockid, succids in enumerate(func.block_exits):
        blockname = _lab(blockid)
        for succid in succids:
          g.edge(blockname, _lab(succid))

  return dot.source


if __name__ == '__main__':
  p = BBProgram(json.load(sys.stdin))
  print(mkdot(p))