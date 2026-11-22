    .module crt0
    .globl _main
    .globl _putc
    .globl l__INITIALIZER
    .globl s__INITIALIZER
    .globl s__INITIALIZED

    .area _CODE

    di
    ld sp, #0xFFFE

    ld hl, #s__INITIALIZER
    ld de, #s__INITIALIZED
    ld bc, #l__INITIALIZER
    ld a, b
    or a, c
    jr z, no_init
    ldir
no_init:

    call _main
halt_loop:
    halt
    jr halt_loop

_putc:
    out (#0x01), a
    ret
