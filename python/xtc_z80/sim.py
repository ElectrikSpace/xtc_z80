"""Simulateur Z80 cycle-accurate côté hôte (gcc) + exécution d'un .bin.

Le cœur est superzazu/z80 (z80/z80.c), le harnais support/sim/main.c fournit
64 Ko de RAM plate, un port console 0x01 et compte les t-states exacts.
"""

import re
import subprocess
from dataclasses import dataclass
from pathlib import Path

from .config import ToolchainConfig

_TSTATES_RE = re.compile(
    r"\[z80sim\] pc=0x([0-9A-Fa-f]+) (HALT|t-state limit reached) after (\d+) t-states"
)


@dataclass
class RunResult:
    """Résultat d'une exécution sur le Z80 simulé."""

    output: str        # texte écrit sur le port console 0x01 (stdout du sim)
    t_states: int     # t-states exacts consommés
    halted: bool      # vrai si le CPU a atteint HALT
    pc: int           # PC final
    returncode: int   # code de retour du simulateur


class Z80Simulator:
    """Construit (si nécessaire) le simulateur et y lance des programmes."""

    def __init__(self, cfg: ToolchainConfig | None = None,
                 sim_main_c: Path | None = None):
        self.cfg = cfg or ToolchainConfig.discover()
        self.sim_main_c = Path(sim_main_c) if sim_main_c else self.cfg.support_dir / "sim" / "main.c"

    def ensure_built(self) -> Path:
        """(Re)compile le simulateur hôte si son binaire est absent ou périmé."""
        sources = [self.sim_main_c, self.cfg.z80_core / "z80.c", self.cfg.z80_core / "z80.h"]
        bin_path = self.cfg.sim_bin
        if bin_path.is_file() and all(
            bin_path.stat().st_mtime >= Path(s).stat().st_mtime for s in sources
        ):
            return bin_path
        bin_path.parent.mkdir(parents=True, exist_ok=True)
        subprocess.run(
            [self.cfg.cc, "-O2", "-std=c99", "-Wall", "-Wextra",
             "-I", self.cfg.z80_core, "-o", bin_path,
             self.sim_main_c, self.cfg.z80_core / "z80.c"],
            check=True,
        )
        return bin_path

    def run(self, program: Path, load_addr: int = 0x0000,
            max_tstates: int = 200_000_000, trace: bool = False,
            timeout_s: float = 600.0) -> RunResult:
        """Charge le .bin à load_addr et exécute jusqu'à HALT (ou max_tstates)."""
        sim = self.ensure_built()
        proc = subprocess.run(
            [sim, Path(program), f"0x{load_addr:04X}", str(max_tstates),
             "1" if trace else "0"],
            capture_output=True, text=True, timeout=timeout_s,
        )
        m = _TSTATES_RE.search(proc.stderr)
        if not m:
            raise RuntimeError(
                f"sortie du simulateur inattendue :\n{proc.stdout}\n{proc.stderr}"
            )
        return RunResult(
            output=proc.stdout,
            t_states=int(m.group(3)),
            halted=m.group(2) == "HALT",
            pc=int(m.group(1), 16),
            returncode=proc.returncode,
        )
