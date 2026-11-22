# tests — xtc matmul on Z80 for all int dtypes (i8 / i16 / i32)

The three dtype variants of `test_xtc_i32.py`'s kernel (only the element
type changes; graph and schedule are identical), compiled for a bare-metal
Z80 with SDCC and run on the cycle-accurate z80 simulator — like
`../hello_world/`, but the payload is xtc-generated. Each variant lives in
its own build/gen directory; every source file is shared.

```
tests/
├── Makefile            # per-dtype rules from one template; see DTYPES
├── gen_matmul.py       # xtc graph -> MLIR -> C (one call per dtype)
├── common/
│   ├── crt0.s          # Z80 crt0 + putc on I/O port 0x01
│   ├── main.c          # bare-metal driver (dtype via -DMATMUL_ELT)
│   ├── sim/main.c      # host z80 simulator harness
│   └── xtc_crt/xtc_crt.h   # bare-metal stub of xtc's CRT header
├── build/<dtype>/      # per-variant sdcc artifacts + run log
└── gen/<dtype>/        # per-variant xtc dumps (MLIR + C) and host artifacts
```

## Usage

```
make test        # build + run all variants, require PASS in each
make run         # build + run all variants (no pass/fail check)
make run-i32     # one variant (i8 / i16 / i32)
make test-i8     # one variant with pass/fail check
make gen         # generate the three C kernels via xtc/MLIR
make clean
```

`make test` runs every variant even if one fails, prints the console output
of each, and exits non-zero if any variant did not print PASS.

## Why K=128 instead of K=512

`test_xtc_i32.py` builds `4x512 @ 512x32`; at K=512, B alone is the whole
(bare-metal) address space, so all variants are generated with K=128:

| variant | A (4×128) | B (128×32) | C (4×32) | t-states |
|---------|-----------|------------|----------|----------|
| i8      | 512 B     | 4 KB       | 128 B    | 18.1 M   |
| i16     | 1 KB      | 8 KB       | 256 B    | 21.7 M   |
| i32     | 2 KB      | 16 KB      | 512 B    | 86.9 M   |

Everything else (ops, schedule: `strip_mine i->2, j->16`, `interchange
[k, i, j, i1, j1]`, C emitter) is identical to `test_xtc_i32.py`; only the
`dtype` of the graph builder changes — `gen "int i8/i16/i32"`.

## Test design

`common/main.c` is shared by the three variants (element type selected by
the Makefile via `-DMATMUL_ELT`, see `common/xtc_crt/xtc_crt.h`):

1. Fills `A[i][k] = i+1` and `B[k][j] = j+1`, so the exact result is
   `C[i][j] = (i+1)·(j+1)·K` — every element of C depends on every k-step,
   so any scheduling/indexing/accumulation bug shows up as a mismatch.
2. Calls the xtc-generated `matmul`.
3. Compares all 4×32 elements against the closed-form reference computed
   in 32-bit and narrowed with the element-type cast, i.e. **mod 2^bits**.
   For i8 the reference wraps (e.g. C[0][0] = -128), which is exactly the
   wrap-around semantics of `arith` on i8 in MLIR — and of the narrowed
   two's-complement results SDCC produces. For i16/i32 the value 16384 is
   exact. Prints `PASS: ...` or `FAIL: ...` on the console port.

## Build notes

- SDCC (z80) cannot parse the GCC-isms emitted for host builds
  (`__restrict`, `__attribute__((unused))`), so `common/xtc_crt/xtc_crt.h`
  is a bare-metal stand-in for the xtc C runtime header (typedefs `int8_t`
  as `signed char`, `int16_t` as 16-bit `int`, `int32_t` as `long`,
  `size_t` as 16-bit `unsigned int`).
- The generated multiplies lower to SDCC's z80 runtime helpers
  (`__mulint` for i8/i16 — note the ~4× speed-up over i32's `__mullong`),
  pulled from `tools/sdcc-4.6.0/share/sdcc/lib/z80/z80.lib`.
- Layout: code at 0x0000, data at 0x8000, stack at 0xFFFE (`common/crt0.s`).
- The host executor in `gen_matmul.py` additionally validates each
  generated kernel on x86 (`CODE: 0`) before it is cross-compiled.

## Adding a variant

Append the dtype to `DTYPES` in the Makefile with its element typedef
(`ELT.<shorthand> := <typedef>`); the rule template instantiates targets
`gen-<s>`, `run-<s>`, `test-<s>`. `gen_matmul.py` accepts the new dtype
once added to its `SHORTHAND` mapping.
