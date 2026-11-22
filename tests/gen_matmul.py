#!/usr/bin/env python
# Generates the matmul C source for one element type through the xtc MLIR
# backend, the same way test_xtc_i32.py does (same graph and schedule; only
# the dtype changes), saving the intermediates (including the generated C)
# under gen/<dtype>/.
#
# Usage: gen_matmul.py {int8|int16|int32}
#
# The graph in test_xtc_i32.py uses I=4, J=32, K=512.  The generated code is
# dimension-agnostic, but the test *data* is not: a 512xJ xN matrix B is
# 16 KB (i8), 32 KB (i16) or the whole 64K (i32) — too big to sit next to
# the code of a bare-metal 64K Z80.  All variants therefore use K=128:
#
#   i8 : A 512 B, B 4 KB,  C 128 B
#   i16: A 1 KB, B 8 KB,  C 256 B
#   i32: A 2 KB, B 16 KB, C 512 B
#
# The exact result C[i][j] = (i+1)*(j+1)*K peaks at 16384:
#   - it fits int32 and int16 exactly;
#   - it wraps for int8, so the on-Z80 check (common/main.c) compares
#     modulo 2^8 — exactly the wrap-around semantics of arith ops on i8
#     in MLIR (and of the narrowed two's-complement result with SDCC).

import sys
from pathlib import Path

import xtc.graphs.xtc.op as O
from xtc.backends.mlir import Backend

SHORTHAND = {"int8": "i8", "int16": "i16", "int32": "i32"}
# accepts both the full dtype and the shorthand as the argument
LOOKUP = {**SHORTHAND, **{v: k for k, v in SHORTHAND.items()}}
I, J, K = 4, 32, 128

ROOT = Path(__file__).parent


def main() -> None:
    if len(sys.argv) != 2 or sys.argv[1] not in LOOKUP:
        sys.exit("usage: gen_matmul.py {" + "|".join(SHORTHAND) + "} (or their shorthands)")
    dtype = LOOKUP[sys.argv[1]]
    short = SHORTHAND[dtype]

    gen_dir = ROOT / "gen" / short
    gen_dir.mkdir(parents=True, exist_ok=True)

    a = O.tensor((I, K), dtype, name="A")
    b = O.tensor((K, J), dtype, name="B")

    with O.graph(name="matmul") as gb:
        O.matmul(a, b, name="C")

    graph = gb.graph
    print(graph)

    impl = Backend(graph)

    sch = impl.get_scheduler()
    sch.strip_mine("i", {"i1": 2})
    sch.strip_mine("j", {"j1": 16})
    sch.interchange(["k", "i", "j", "i1", "j1"])
    sched = sch.schedule()

    comp = impl.get_compiler(
        target="c",
        shared_lib=True,
        print_source_ir=True,
        print_transformed_ir=True,
        dump_file=f"{gen_dir}/matmul_{short}_mlir",
        save_temps=True,
        save_temps_dir=f"{gen_dir}",
    )
    module = comp.compile(sched)
    executor = module.get_executor(validate=True)
    res = executor.execute()
    print(f"CODE: {res}")
    assert res == 0
    generated = gen_dir / f"matmul_{short}_mlir.c"
    assert generated.is_file(), "generated C is missing"
    print(f"generated {generated}")


if __name__ == "__main__":
    main()
