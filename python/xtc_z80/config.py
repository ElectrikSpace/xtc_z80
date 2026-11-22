"""Chemins et réglages de la chaîne d'outils (SDCC z80 + cœur Z80 + xtc).

Tout est découvert depuis la racine du projet : ce module n'a pas besoin de
configuration a priori et fonctionne pour n'importe quel exemple.
"""

from dataclasses import dataclass
from pathlib import Path

_SDCC_VERSION = "sdcc-4.6.0"


def project_root() -> Path:
    """Racine du dépôt (python/xtc_z80/config.py -> trois niveaux au-dessus)."""
    return Path(__file__).resolve().parents[2]


@dataclass(frozen=True)
class ToolchainConfig:
    """Tous les chemins de la chaîne z80 + options de lien SDCC par défaut."""

    project_root: Path
    sdcc_bin: Path
    sdcc_z80_lib: Path
    z80_core: Path
    support_dir: Path       # crt0.s, xtc_crt/xtc_crt.h, sim/main.c
    sim_bin: Path
    cc: str = "gcc"
    code_loc: int = 0x0000
    data_loc: int = 0x8000

    @classmethod
    def discover(cls, root: Path | None = None, sim_bin: Path | None = None) -> "ToolchainConfig":
        """Cherche les outils dans le layout du dépôt (tools/, z80/, python/)."""
        root = Path(root).resolve() if root else project_root()
        sdcc = root / "tools" / _SDCC_VERSION / "bin"
        for tool in ("sdcc", "sdasz80", "sdobjcopy"):
            if not (sdcc / tool).is_file():
                raise FileNotFoundError(
                    f"outil {tool} introuvable dans {sdcc} ; "
                    "lance scripts/fetch-deps.sh"
                )
        z80_core = root / "z80"
        if not (z80_core / "z80.c").is_file():
            raise FileNotFoundError(f"cœur Z80 introuvable dans {z80_core}")
        return cls(
            project_root=root,
            sdcc_bin=sdcc,
            sdcc_z80_lib=root / "tools" / _SDCC_VERSION / "share" / "sdcc" / "lib" / "z80" / "z80.lib",
            z80_core=z80_core,
            support_dir=Path(__file__).resolve().parent / "support",
            sim_bin=Path(sim_bin) if sim_bin else root / "build" / "python" / "z80sim",
        )
