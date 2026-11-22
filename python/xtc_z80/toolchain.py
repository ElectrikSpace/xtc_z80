"""Invocations SDCC / sdasz80 / sdobjcopy pour croiser-compiler vers le Z80.

Reproduit en Python les étapes du Makefile de ../tests : compilation C ->
.rel, assemblage du crt0, édition de liens (+ z80.lib pour les helpers
__mulint / __mullong) et conversion ihex -> binaire brut.
"""

import shutil
import subprocess
from pathlib import Path

from .config import ToolchainConfig


class ToolchainError(RuntimeError):
    """Une commande de la chaîne croisée a échoué."""


def _run(cmd) -> subprocess.CompletedProcess:
    cmd = [str(c) for c in cmd]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        raise ToolchainError(
            f"commande échouée ({proc.returncode}) : {' '.join(cmd)}\n"
            f"stdout:\n{proc.stdout}\nstderr:\n{proc.stderr}"
        )
    return proc


class Z80Toolchain:
    """Croisé-compile et lie des sources pour un Z80 bare-metal (SDCC)."""

    def __init__(self, cfg: ToolchainConfig):
        self.cfg = cfg

    # --- options communes -------------------------------------------------

    def _sdcc_base_flags(self) -> list:
        cfg = self.cfg
        return [
            cfg.sdcc_bin / "sdcc",
            "-mz80", "--std-c11", "--nostdinc", "--nostdlib", "--no-std-crt0",
            "--code-loc", f"0x{cfg.code_loc:04X}",
            "--data-loc", f"0x{cfg.data_loc:04X}",
        ]

    # --- étapes -----------------------------------------------------------

    def compile_c(
        self,
        source: Path,
        out_rel: Path,
        defines: dict[str, str] | None = None,
        include_dirs: list[Path] | None = None,
    ) -> Path:
        """Compile un fichier C en .rel (sdcc -mz80, sans libc ni crt0)."""
        out_rel = Path(out_rel)
        out_rel.parent.mkdir(parents=True, exist_ok=True)
        cmd = list(self._sdcc_base_flags())
        for inc in include_dirs or [self.cfg.support_dir]:
            cmd += ["-I", Path(inc)]
        for name, value in (defines or {}).items():
            cmd.append(f"-D{name}={value}" if value is not None else f"-D{name}")
        cmd += ["-c", "-o", out_rel, Path(source)]
        _run(cmd)
        return out_rel

    def assemble(self, asm_source: Path, out_rel: Path, workdir: Path | None = None) -> Path:
        """Assemble le crt0 (sdasz80) ; le fichier est d'abord recopié dans
        workdir pour que les fichiers annexes (.lst/.sym) n'atterrissent pas
        à côté de la source."""
        out_rel = Path(out_rel)
        workdir = Path(workdir) if workdir else out_rel.parent
        workdir.mkdir(parents=True, exist_ok=True)
        staged = workdir / Path(asm_source).name
        shutil.copyfile(asm_source, staged)
        _run([self.cfg.sdcc_bin / "sdasz80", "-xlos", "-g", "-o", out_rel, staged])
        return out_rel

    def link(self, rel_files: list[Path], out_ihx: Path, extra_libs: list[Path] | None = None) -> Path:
        """Édite les .rel en .ihx ; z80.lib est liée par défaut (les
        multiplications générées par xtc appellent __mulint/__mullong)."""
        out_ihx = Path(out_ihx)
        out_ihx.parent.mkdir(parents=True, exist_ok=True)
        libs = extra_libs if extra_libs is not None else [self.cfg.sdcc_z80_lib]
        cmd = self._sdcc_base_flags() + ["-o", out_ihx]
        cmd += [Path(r) for r in rel_files] + [Path(l) for l in libs]
        _run(cmd)
        return out_ihx

    def ihex_to_bin(self, ihx: Path, out_bin: Path) -> Path:
        """Convertit le .ihx en binaire brut chargeable par le simulateur."""
        out_bin = Path(out_bin)
        out_bin.parent.mkdir(parents=True, exist_ok=True)
        _run([self.cfg.sdcc_bin / "sdobjcopy", "-I", "ihex", "-O", "binary",
              Path(ihx), out_bin])
        return out_bin

    # --- pipeline complet ---------------------------------------------------

    def build_binary(
        self,
        kernel_c: Path,
        main_c: Path,
        out_bin: Path,
        defines: dict[str, str] | None = None,
    ) -> Path:
        """main.c + noyau xtc + crt0 -> .bin bare-metal prêt à charger."""
        out_dir = Path(out_bin).parent
        out_dir.mkdir(parents=True, exist_ok=True)
        crt0 = self.assemble(self.cfg.support_dir / "crt0.s", out_dir / "crt0.rel")
        main = self.compile_c(main_c, out_dir / "main.rel", defines=defines)
        kernel = self.compile_c(kernel_c, out_dir / f"{Path(kernel_c).stem}.rel")
        ihx = self.link([crt0, main, kernel], out_dir / "matmul.ihx")
        return self.ihex_to_bin(ihx, out_bin)
