## Dead code elimination using data-flow

Goal: To find dead instructions that can just be removed.

* Run a pass of data-flow analysis to compute reaching definitions at the end
  of each block.
* Merge the end-of-block reaching def sets together into one live-at-some-point
  definitions set L.
* Scan the program and remove all definitions not in L.

# Reverse post-ordering of CFGs

AKA topological sorting guarantees that an iterative data flow analyzer will
visit each node of the CFG only once in a _reducible CFG_. A reducible CFG
is one which only has natural loops.