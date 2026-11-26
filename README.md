# xtc-z80

Run XTC kernels on a cycle-accurate simulated Z80, with no OS
(bare metal) — from graph definition down to the exact t-state count.

## Architecture

```
XTC (matmul graph, MLIR backend target='c')       ->  C code
main.c (bare-metal driver)                        ->  SDCC -mz80  ->  Z80 .bin
cycle-accurate Z80 simulator (superzazu/z80)     ->  console + exact t-states
```

- **XTC** (`xtc/`, submodule) — graph definition and scheduling; the
  existing MLIR backend with `target='c'` generates the kernel C code,
  with no dedicated Z80 backend or target.
- **C code generation** (`python/xtc_z80/cgen.py`,
  `xtc_backend.py`) — Python bridge to XTC: compiles the graph to C and
  renders the bare-metal `main.c` from a template.
- **Z80 simulator** (`z80/` + harness `sim/main.c`) —
  `superzazu/z80` core (cycle-accurate) compiled on the host; 64 KiB of
  flat RAM, console on I/O port 0x01, exact t-state counting up to
  `HALT`.
- **Wrapper and C runtime** (`crt0.s`, `xtc_crt/xtc_crt.h`) — bare-metal
  startup (SP init, initialized-data copy, `call _main`,
  `halt`), `putc` on port 0x01 and SDCC stub for XTC's CRT header;
  `toolchain.py` drives SDCC / sdasz80 / sdobjcopy
  (cross-compilation -> raw binary).

## Usage

```sh
./scripts/fetch-deps.sh   # fetches SDCC (prebuilt release); requires gh to be logged in
make -C tests test        # build + run of the i8 / i16 / i32 variants, requires PASS
../venv/bin/python examples/matmul_z80.py   # 100% Python example
```

## Contents

- `tests/` — tests: XTC matmul (i8 / i16 / i32) compiled and run on the
  simulated Z80, with PASS/FAIL verification.
- `examples/` — examples, including `matmul_z80.py` (full pipeline
  driven from Python).

Details for each component are in the local `README.md` files
(`python/`, `tests/`, `z80/`).
