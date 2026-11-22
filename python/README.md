# python/ — utilitaires xtc → Z80 pilotés depuis Python

Bibliothèque réutilisable par tous les exemples (comme
`../examples/matmul_z80.py`) pour la chaîne complète **sans** créer de
backend ni de target XTC dédiés :

```
graphe xtc (backend MLIR, target='c')  ->  code C
main.c bare-metal (template rendu)      ->  SDCC -mz80  ->  .bin
simulateur Z80 cycle-accurate (gcc)     ->  console + t-states exacts
```

## Modules (`xtc_z80`)

| module            | rôle |
|-------------------|------|
| `config.py`       | `ToolchainConfig.discover()` : chemin des outils (racine du dépôt : `tools/sdcc-4.6.0`, `z80/`) |
| `toolchain.py`    | `Z80Toolchain` : `compile_c`, `assemble` (crt0), `link` (+ `z80.lib`), `ihex_to_bin`, et le pipeline prêt à l'emploi `build_binary()` |
| `sim.py`          | `Z80Simulator` : `ensure_built()` (gcc) puis `run()` → `RunResult(output, t_states, halted, pc)` |
| `xtc_backend.py`  | `compile_graph_to_c()` : graphe + scheduler → C via `Backend(target='c')`, avec validation hôte du noyau (`executor.execute()` doit rendre `CODE: 0`) |
| `cgen.py`         | `render()` (template `string.Template`, sans conflit avec la syntaxe C) + `CONSOLE_C` (printf minimal via `putc` sur le port I/O 0x01) |
| `support/`        | fichiers C embarqués : `crt0.s`, `xtc_crt/xtc_crt.h` (stub SDCC de l'en-tête CRT de xtc, **sans** typedef de noyau — le driver amène le sien), `sim/main.c` (harnais : 64 Ko RAM, console 0x01, comptage t-states) |

## Utilisation depuis un exemple

```python
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "python"))

from xtc_z80 import (ToolchainConfig, Z80Toolchain, Z80Simulator,
                     compile_graph_to_c, render, CONSOLE_C)

kernel = compile_graph_to_c(graph, "mon_noyau", workdir, prepare_scheduler)
main_c = render(MAIN_TEMPLATE, workdir / "main.c", kernel=..., console_lib=CONSOLE_C)
cfg = ToolchainConfig.discover()
binary = Z80Toolchain(cfg).build_binary(kernel, main_c, workdir / "prog.bin")
result = Z80Simulator(cfg).run(binary)   # .output, .t_states, .halted
```

## Convention

- Artéfacts sous `build/examples/<nom>/` (ignorés par git, cf. `.gitignore`) :
  dumps MLIR + C xtc dans `xtc/`, sources SDCC et `matmul.bin` à la racine.
- Simulateur hôte partagé : `build/python/z80sim`.
- K des matmuls limité à 128 (contre 512 dans `../test_xtc_i32.py`) pour que
  les opérandes tiennent dans les 64 Ko du Z80 — cf. `../tests/README.md`.
- `support/` est la copie détenue par le package de `../tests/common/`
  (mêmes fichiers, la CRT en moins kernel-spécifique).
