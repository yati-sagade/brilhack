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

# Loop-invariant code motion

Consider:

  @main() {
    .start:
    let i: int = 0;
    let incr: int = 1;
    .loop:
    let done: i = eq i, 10;
    cond done .break .next;
    .next:
    let x: int = add incr, incr;
    let i: int = add i, x;
    .break:
  }

The `let x: int = add incr, incr` statement is invariant for this loop, and
can be moved outside. But consider:


  @main(i: int) {
    .start:
    let incr: int = 1;
    .loop:
    let done: i = eq i, 10;
    cond done .break .next;
    .next:
    let x: int = add incr, incr;
    let i: int = add i, x;
    .break:
    print i;
    print x;
  }

Here, there is no way to know if the loop will even execute one iteration. If it
does not, then setting `x = add incr, incr;` before the loop will produce an
incorrect result when later printing x.

When is an instruction LI?

* When all of the following hold:

  - It is a value op (as opposed to an effect op).
  - Each of its arguments either:
    - Has all reaching definitions from outside the loop, OR,
    - There is exactly one definition, and already marked LI.

When is it safe to move an LI instr outside the loop?

  - Definition dominates all its uses,
  - No other definitions of the same variable,
  - Dominates all loop exits (so would be computed anyway).

The last condition might be relaxed if:

  - If the destination var is dead after the loop, and
  - It can't throw an exception.

This is a common theme with speculative optimizations that do extra work hoping
it will be useful for the common case.
