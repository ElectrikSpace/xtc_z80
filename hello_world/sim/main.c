#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "z80.h"

#define MEM_SIZE 0x10000
#define CONSOLE_PORT 0x01

static uint8_t mem[MEM_SIZE];

static uint8_t read_byte(void *userdata, uint16_t addr) {
  (void)userdata;
  return mem[addr];
}

static void write_byte(void *userdata, uint16_t addr, uint8_t value) {
  (void)userdata;
  mem[addr] = value;
}

static uint8_t port_in(z80 *z, uint8_t port) {
  (void)z;
  (void)port;
  return 0xFF;
}

static void port_out(z80 *z, uint8_t port, uint8_t value) {
  (void)z;
  if (port == CONSOLE_PORT) {
    fputc(value, stdout);
    fflush(stdout);
  }
}

int main(int argc, char **argv) {
  if (argc < 2) {
    fprintf(stderr, "usage: %s <program.bin> [load_addr] [max_tstates] [trace]\n",
            argv[0]);
    return 2;
  }

  const char *path = argv[1];
  uint16_t load_addr = argc > 2 ? (uint16_t)strtoul(argv[2], NULL, 0) : 0x0000;
  unsigned long max_cyc = argc > 3 ? strtoul(argv[3], NULL, 0) : 200000000UL;
  int trace = argc > 4 ? atoi(argv[4]) : 0;

  FILE *f = fopen(path, "rb");
  if (!f) {
    perror(path);
    return 1;
  }
  fseek(f, 0, SEEK_END);
  long size = ftell(f);
  fseek(f, 0, SEEK_SET);
  if (size < 0 || (long)load_addr + size > MEM_SIZE) {
    fprintf(stderr, "program too big for 64K address space\n");
    return 1;
  }
  if (fread(mem + load_addr, 1, (size_t)size, f) != (size_t)size) {
    fprintf(stderr, "failed to read %s\n", path);
    return 1;
  }
  fclose(f);

  z80 z;
  z80_init(&z);
  z.read_byte = read_byte;
  z.write_byte = write_byte;
  z.port_in = port_in;
  z.port_out = port_out;
  z.pc = load_addr;
  z.sp = 0xFFFE;

  while (!z.halted && z.cyc < max_cyc) {
    if (trace)
      z80_debug_output(&z);
    z80_step(&z);
  }

  fprintf(stderr, "[z80sim] pc=0x%04X %s after %lu t-states\n", z.pc,
          z.halted ? "HALT" : "t-state limit reached", z.cyc);
  return z.halted ? 0 : 1;
}
