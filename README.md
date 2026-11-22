# z80-xtc-matmul

Petit projet : exécuter une petite multiplication de matrices compilée avec
[XTC](https://github.com/xtc-tools/xtc) sur un **Z80 simulé, cycle-accurate**,
sans OS (bare metal).

## Chaîne visée

```
XTC (DSL matmul, XTC_MLIR_TARGET=c)  -->  code C
SDCC -mz80 (bare metal, sans OS)     -->  hello.bin / matmul.bin (binaire brut Z80)
z80sim (cœur Z80 cycle-accurate)     -->  exécution + nombre exact de t-states
```

## Choix du simulateur : `superzazu/z80`

Cœur Z80 en C99, embarquable, licence MIT, un seul fichier (`z80.c` + `z80.h`).

- **Cycle-accurate** : compte exact des t-states par instruction. Preuve :
  le test `zexall` (5 764 169 747 instructions, toutes les opcodes documentées
  et non documentées) s'exécute en **46 734 978 649 cycles, expected=...,
  diff=0** (voir `github__superzazu__z80/README.md` ; vérifié localement avec
  `make -C github__superzazu__z80 && ./z80_tests`).
- **Sans OS / bare metal** : on fournit soi-même les callbacks
  `read_byte` / `write_byte` / `port_in` / `port_out` (64 Ko de RAM plate +
  port console 0x01 dans `sim/main.c`) ; on charge un `.bin` à une adresse et
  on lance `z80_step()` jusqu'au `HALT`. Compteur `z.cyc` = t-states exacts.

Alternatives envisagées : `anotherlin/z80emu` (très complet, passe aussi
zexall, mais API par macros dans `z80user.h`), `stevecheckoway/libzel`
(cycle-accurate en t-states, API callback), `z80ex` (GPL-2.0),
`michalhucik/z80-mz800` (cpu-z80, C99, cycle-accurate). Toutes valides ;
`superzazu/z80` est le plus simple à embarquer pour du bare metal.

## Choix du compilateur C pour Z80 : SDCC 4.6.0

`sdcc -mz80 --nostdinc --nostdlib --no-std-crt0 --code-loc 0x0000
--data-loc 0x8000` + un `crt0.s` maison (init SP, copie `_INITIALIZER` ->
`_INITIALIZED`, `call _main`, `halt`), puis `sdobjcopy -I ihex -O binary`.
Binaire brut, aucune dépendance à un OS. Binaires précompilés téléchargés
depuis les releases de `retropack/sdcc` (statiques, x86_64/aarch64).

## Utilisation

```sh
./scripts/fetch-deps.sh   # clone le cœur Z80 + télécharge SDCC (nécessite gh connecté)
make run                  # compile z80sim + hello.bin, puis exécute sur le Z80 simulé
```

Sortie constatée :

```
Hello from Z80 (SDCC -> z80sim)!
[z80sim] pc=0x0017 HALT after 4004 t-states
```

Le simulateur : `build/z80sim <prog.bin> [load_addr] [max_tstates] [trace]`
(affiche les t-states exacts consommés ; `trace=1` pour le pas-à-pas).

## Layout

```
Makefile               cibles all / run / clean
sim/main.c             harness : RAM 64 Ko, port 0x01 = console, boucle z80_step
src/hello.c            hello world en C (étape 1)
src/crt0.s             démarrage bare metal + putc (port 0x01)
scripts/fetch-deps.sh  récupère les dépendances (gh)
github__superzazu__z80 cœur Z80 cycle-accurate (clone)
tools/sdcc-4.6.0/      SDCC précompilé (binaires release)
```

## Étape suivante (matmul XTC)

XTC expose une cible MLIR `c` (`XTC_MLIR_TARGET=c`) : on compile le graphe
`matmul` en C, puis ce C passe dans la chaîne ci-dessus (SDCC -> `.bin` ->
z80sim) pour mesurer le temps d'exécution en t-states exacts sur le Z80 simulé.
