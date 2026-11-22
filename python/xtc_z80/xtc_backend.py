"""Pont vers xtc : graphe -> code C via le backend MLIR (target='c').

Sans créer de backend ni de target XTC dédiés : on réutilise le Backend
MLIR existant exactement comme test_xtc_i32.py en natif (graphes, scheduler,
get_compiler(target='c')), puis on récupère le C généré pour la suite de la
chaîne (SDCC z80, simulateur).
"""

from collections.abc import Callable
from pathlib import Path

from xtc.backends.mlir import Backend


class XTCCompileError(RuntimeError):
    """La compilation xtc -> C a échoué (ou le noyau est invalide sur l'hôte)."""


def compile_graph_to_c(
    graph,
    name: str,
    out_dir: Path,
    prepare_scheduler: Callable | None = None,
    *,
    validate: bool = True,
    verbose: bool = False,
) -> Path:
    """Compile un graphe xtc en C ; retourne le chemin du .c généré.

    graph             : graphe xtc (déjà construit, cf. xtc.graphs.xtc.op)
    name              : base des fichiers de dump (name.c, name.mlir, ...)
    out_dir           : dossier des artéfacts xtc (créé si besoin)
    prepare_scheduler : callback qui applique strip_mine/interchange/... au
                        scheduler avant schedule() ; None = aucun scheduling
    validate          : exécute en plus le module sur l'hôte (cf.
                        executor.execute()) pour valider le noyau — CODE: 0
    verbose           : imprime les IR avant/après transform, comme
                        test_xtc_i32.py
    """
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    impl = Backend(graph)
    sch = impl.get_scheduler()
    if prepare_scheduler is not None:
        prepare_scheduler(sch)
    sched = sch.schedule()

    comp = impl.get_compiler(
        target="c",
        shared_lib=True,
        print_source_ir=verbose,
        print_transformed_ir=verbose,
        dump_file=str(out_dir / name),
        save_temps=True,
        save_temps_dir=str(out_dir),
    )
    module = comp.compile(sched)

    if validate:
        res = module.get_executor(validate=True).execute()
        if res != 0:
            raise XTCCompileError(f"validation hôte du noyau échouée (CODE: {res})")

    c_path = out_dir / f"{name}.c"
    if not c_path.is_file():
        raise XTCCompileError(f"code C généré introuvable : {c_path}")
    return c_path
