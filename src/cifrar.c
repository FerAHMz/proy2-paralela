// Cifra un archivo de texto con DES (ECB) usando una llave de 56 bits.
// Uso: ./cifrar <llave> <entrada.txt> <salida.bin>
// El texto se rellena con espacios hasta un múltiplo de 8 bytes.
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include "des_util.h"

int main(int argc, char *argv[]){
  if(argc != 4){
    fprintf(stderr, "Uso: %s <llave> <entrada.txt> <salida.bin>\n", argv[0]);
    return 1;
  }
  long key = strtol(argv[1], NULL, 10);
  if(key < 0 || key >= (1L << 56)){
    fprintf(stderr, "La llave debe estar en [0, 2^56)\n");
    return 1;
  }

  FILE *in = fopen(argv[2], "rb");
  if(!in){ perror(argv[2]); return 1; }
  fseek(in, 0, SEEK_END);
  int len = ftell(in);
  rewind(in);

  int padded = (len + 7) / 8 * 8;
  char *buf = malloc(padded);
  fread(buf, 1, len, in);
  fclose(in);
  memset(buf + len, ' ', padded - len);

  encrypt(key, buf, padded);

  FILE *out = fopen(argv[3], "wb");
  if(!out){ perror(argv[3]); return 1; }
  fwrite(buf, 1, padded, out);
  fclose(out);

  printf("Llave %ld: %d bytes de texto -> %d bytes cifrados en %s\n", key, len, padded, argv[3]);
  free(buf);
  return 0;
}
