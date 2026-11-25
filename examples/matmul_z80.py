#!/home/sylvain/Documents/testons/xtc_z80/venv/bin/python
# RUN: ../venv/bin/python %s 2>&1 | tail -3

"""Exemple 100 % Python : matmul xtc compilé sur C puis exécuté sur le Z80.

Équivalent de ../test_xtc_i32.py (matmul i32 natif), mais la cible est le Z80
simulé cycle-accurate — sans créer de backend ni de target XTC : la target
MLIR 'c' de xtc fournit le code C, et tout l'outillage (génération du main,
croix-compilation SDCC, exécution du simulateur) est piloté depuis ce seul
script via les utilitaires de ../python.

Chaîne :
  xtc (graphe + scheduling, target='c') -> matmul_<iN>.c
  + main.c rendu depuis MAIN_C_TEMPLATE   -> SDCC -mz80 -> .bin bare-metal
  -> simulateur Z80 (superzazu/z80)        -> sortie console + t-states

Données (comme tests/common/main.c) : A[i][k]=i+1, B[k][j]=j+1, donc
C[i][j]=(i+1)*(j+1)*K, comparé modulo le type d'élément (2^bits) — i8
wrappe, i16/i32 sont exacts. K=128 au lieu de 512 pour que B tienne dans
les 64 Ko du Z80 (cf. tests/README.md).

Usage :
  ./venv/bin/python examples/matmul_z80.py                # int32 par défaut
  ./venv/bin/python examples/matmul_z80.py --dtype int8
  ./venv/bin/python examples/matmul_z80.py --verbose      # dumps MLIR complets
"""

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "python"))

import xtc.graphs.xtc.op as O

from xtc_z80 import (
    CONSOLE_C,
    ToolchainConfig,
    Z80Simulator,
    Z80Toolchain,
    compile_graph_to_c,
    project_root,
    render,
)

# Même kernel que test_xtc_i32.py : seul le dtype (et la profondeur de
# réduction K, réduite pour entrer dans l'espace d'adressage du Z80) change.
I, J, K = 4, 32, 128
DTYPE2ELT = {"int8": "int8_t", "int16": "int16_t", "int32": "int32_t"}
SHORTHAND = {"int8": "i8", "int16": "i16", "int32": "i32"}

# --- main.c bare-metal : rendu via python/xtc_z80/cgen.py -------------------
# La fonction du noyau porte le nom du graphe ('matmul') ; les helpers
# d'impression et le stub CRT viennent du package.

MAIN_C_TEMPLATE = """\
/* main.c bare-metal Z80 — généré par examples/matmul_z80.py.
 *
 * Driver du noyau xtc ${kernel} : remplit A et B, appelle le noyau, compare
 * C à (i+1)*(j+1)*K rétréci au type d'élément (comparaison modulo 2^bits,
 * cf. tests/common/main.c). Console sur le port I/O 0x01 (crt0.s).
 */
#include "xtc_crt/xtc_crt.h"

#define I ${I}
#define J ${J}
#define K ${K}

typedef ${elt} matmul_elt;

extern void ${kernel}(matmul_elt *a, matmul_elt *b, matmul_elt *c);

static matmul_elt A[I][K];
static matmul_elt B[K][J];
static matmul_elt C[I][J];

${console_lib}

void main(void) {
  for (int i = 0; i < I; i++)
    for (int k = 0; k < K; k++)
      A[i][k] = i + 1;

  for (int k = 0; k < K; k++)
    for (int j = 0; j < J; j++)
      B[k][j] = j + 1;

  ${kernel}((matmul_elt *)A, (matmul_elt *)B, (matmul_elt *)C);

  unsigned int mismatches = 0;
  int fi = 0, fj = 0;
  int32_t fgot = 0, fexp = 0;
  for (int i = 0; i < I; i++) {
    for (int j = 0; j < J; j++) {
      /* Référence exacte en 32 bits, puis rétrécie : la comparaison est
       * modulo le type d'élément (arith iN wrappe dans MLIR comme avec
       * SDCC en deux's complément). */
      int32_t expected = (int32_t)(i + 1) * (j + 1) * K;
      matmul_elt narrowed = (matmul_elt)expected;
      if (C[i][j] != narrowed) {
        if (mismatches == 0) {
          fi = i;
          fj = j;
          fgot = C[i][j];
          fexp = narrowed;
        }
        mismatches++;
      }
    }
  }

  if (mismatches == 0) {
    puts_raw("PASS: matmul ");
    put_dec(I);
    putc('x');
    put_dec(K);
    putc('x');
    put_dec(J);
    putc(' ');
    puts_raw("i");
    put_dec(sizeof(matmul_elt) * 8);
    puts_raw(" on Z80 (sdcc + xtc)\\r\\n");
  } else {
    puts_raw("FAIL: mismatches=");
    put_dec(mismatches);
    puts_raw(" first at i=");
    put_dec((unsigned int)fi);
    puts_raw(" j=");
    put_dec((unsigned int)fj);
    puts_raw(" got=0x");
    put_hex32(fgot);
    puts_raw(" expected=0x");
    put_hex32(fexp);
    puts_raw("\\r\\n");
  }
}
"""


def build_graph(dtype: str):
    """Construit le même graphe matmul que test_xtc_i32.py (dtype près)."""
    a = O.tensor((I, K), dtype, name="A")
    b = O.tensor((K, J), dtype, name="B")
    with O.graph(name="matmul") as gb:  # -> fonction 'matmul' dans le C
        O.matmul(a, b, name="C")
    return gb.graph


def schedule_matmul(sch) -> None:
    """Même schedule que test_xtc_i32.py : strip-mine i/j + interchange."""
    sch.strip_mine("i", {"i1": 4})
    sch.strip_mine("j", {"j1": 1})
    sch.interchange(["k", "i", "j", "i1", "j1"])


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--dtype", choices=sorted(DTYPE2ELT), default="int32",
                        help="type d'élément du matmul (défaut : int32)")
    parser.add_argument("--verbose", action="store_true",
                        help="affiche les IR MLIR avant/après transform")
    args = parser.parse_args()

    short = SHORTHAND[args.dtype]
    workdir = project_root() / "build" / "examples" / f"matmul_{short}"
    print(f"[example] dtype={args.dtype}  workdir={workdir}")

    # 1. graphe xtc -> C (target 'c'), avec validation hôte du noyau
    graph = build_graph(args.dtype)
    print(graph)
    kernel_c = compile_graph_to_c(
        graph,
        name=f"matmul_{short}",
        out_dir=workdir / "xtc",
        prepare_scheduler=schedule_matmul,
        verbose=args.verbose,
    )
    print(f"[example] noyau C généré : {kernel_c}")

    # 2. main.c bare-metal (template du driver)
    main_c = render(
        MAIN_C_TEMPLATE,
        workdir / "main.c",
        kernel="matmul",
        elt=DTYPE2ELT[args.dtype],
        I=I, J=J, K=K,
        console_lib=CONSOLE_C,
    )
    print(f"[example] driver généré  : {main_c}")

    # 3. croix-compilation SDCC z80 : crt0 + main + noyau -> .bin
    cfg = ToolchainConfig.discover()
    tc = Z80Toolchain(cfg)
    binary = tc.build_binary(kernel_c, main_c, workdir / "matmul.bin")
    print(f"[example] binaire       : {binary}")

    # 4. exécution sur le Z80 simulé (cycle-accurate)
    sim = Z80Simulator(cfg)
    result = sim.run(binary, load_addr=cfg.code_loc)

    print(result.output, end="")
    print(f"[example] {result.t_states} t-states, pc=0x{result.pc:04X}, "
          f"halted={result.halted}")

    passed = result.output.startswith("PASS") and result.halted
    print(f"[example] {'PASS' if passed else 'FAILED'}")
    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(main())
