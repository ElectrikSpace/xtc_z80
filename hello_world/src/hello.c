extern void putc(char c);

static char msg[] = "Hello from Z80 (SDCC -> z80sim)!\r\n";

void main(void) {
  char *p = msg;
  while (*p) {
    putc(*p);
    p++;
  }
}
