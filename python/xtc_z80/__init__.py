"""Utilitaires Python xtc -> Z80 : graphe xtc (target C) -> SDCC z80 ->
simulateur Z80 cycle-accurate, pilotables depuis un seul script.

Réutilisables entre exemples :
  - ToolchainConfig  : découverte des outils (tools/sdcc-4.6.0, z80/)
  - Z80Toolchain      : sdcc / sdasz80 / sdobjcopy (compile_c, link, ...)
  - Z80Simulator      : build + run du simulateur hôte (build/python/z80sim)
  - compile_graph_to_c: graphe xtc -> C via le backend MLIR target='c'
  - render / CONSOLE_C: génération du main.c bare-metal depuis un template

Les fichiers de support C embarqués dans le package : support/crt0.s,
support/xtc_crt/xtc_crt.h (stub SDCC de l'en-tête CRT de xtc) et
support/sim/main.c (harnais du simulateur, RAM 64K + console port 0x01) ;
ce sont les mêmes que tests/common/, détenus par le package pour être
indépendants de l'infrastructure de tests.
"""

from .config import ToolchainConfig, project_root
from .cgen import CONSOLE_C, render
from .sim import RunResult, Z80Simulator
from .toolchain import ToolchainError, Z80Toolchain
from .xtc_backend import XTCCompileError, compile_graph_to_c

__all__ = [
    "CONSOLE_C",
    "RunResult",
    "ToolchainConfig",
    "ToolchainError",
    "XTCCompileError",
    "Z80Simulator",
    "Z80Toolchain",
    "compile_graph_to_c",
    "project_root",
    "render",
]
