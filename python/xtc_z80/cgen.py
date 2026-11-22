"""Génération du main.c bare-metal à partir d'un template.

Le contenu du driver (init des données, vérification) dépend de l'exemple ;
ce module fournit le mécanisme (rendu + écriture) et les briques C
réutilisables (console sur le port 0x01, fournie par crt0.s).
"""

import string
from pathlib import Path

#: Briques C communes : console via putc sur le port I/O 0x01 (crt0.s).
#: Convient à tout main.c bare-metal du projet.
CONSOLE_C = """\
extern void putc(char c);

static void puts_raw(const char *s) {
  while (*s)
    putc(*s++);
}

static void put_hex8(unsigned int v) {
  static const char digits[] = "0123456789ABCDEF";
  putc(digits[(v >> 4) & 0xF]);
  putc(digits[v & 0xF]);
}

static void put_hex32(int32_t value) {
  unsigned long v = (unsigned long)value;
  put_hex8((unsigned int)((v >> 24) & 0xFF));
  put_hex8((unsigned int)((v >> 16) & 0xFF));
  put_hex8((unsigned int)((v >> 8) & 0xFF));
  put_hex8((unsigned int)(v & 0xFF));
}

static void put_dec(unsigned int v) {
  char buf[6];
  int n = 0;
  do {
    buf[n++] = (char)('0' + v % 10);
    v /= 10;
  } while (v && n < 5);
  while (n)
    putc(buf[--n]);
}
"""


def render(template: str, dst: Path, **context) -> Path:
    """Rend un template C ($variable, style string.Template) et l'écrit.

    Le C n'utilise pas '$', donc string.Template est sans ambiguïté ici.
    substitute() (strict) attrape les placeholders mal orthographiés.
    """
    text = string.Template(template).substitute(**context)
    dst = Path(dst)
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_text(text)
    return dst
