/* Bare-metal stand-in for the xtc C runtime header (xtc_crt/xtc_crt.h).
 *
 * The real header (from the MLIR install) pulls in the host libc; on the Z80
 * we build with sdcc --nostdinc --nostdlib, so the generated xtc C code gets
 * this minimal version instead.  It also maps away two GCC-isms SDCC's
 * C front-end does not accept ("__restrict" and "__attribute__((unused))"
 * on parameters).
 *
 * The three test variants (i8/i16/i32) share this header and common/main.c;
 * the element type is selected by the Makefile with -DMATMUL_ELT=intN_t
 * (int32_t by default when the driver is built by hand).
 */
#ifndef XTC_CRT_HEADER
#define XTC_CRT_HEADER

/* SDCC for z80: char is 8-bit, int is 16-bit, long is 32-bit. */
typedef signed char int8_t;
typedef int int16_t;
typedef signed long int32_t;
typedef unsigned int size_t;

/* Kernel element type (what common/main.c allocates and checks). */
#ifndef MATMUL_ELT
#define MATMUL_ELT int32_t
#endif
typedef MATMUL_ELT matmul_elt;

#define NULL ((void *)0)

/* SDCC does not support restrict; it is irrelevant without an optimizer. */
#define __restrict

/* Only used in generated code on function parameters (dead declarations). */
#define __attribute__(x)

#endif /* XTC_CRT_HEADER */
