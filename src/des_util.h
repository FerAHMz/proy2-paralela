// Versión corregida de decrypt/encrypt/tryKey de bruteforce.c.
// Cambios respecto al original:
//  - la llave y la máscara son unsigned long: evita desplazamientos de int
//    y desbordamiento con signo al convertir llaves altas de 56 bits.
//  - ecb_crypt recibe len (múltiplo de 8) en vez de 16 fijo, así se cifra todo el texto.
#ifndef DES_UTIL_H
#define DES_UTIL_H

#include <string.h>
#include <rpc/des_crypt.h>

// Reparte los 56 bits de key en 8 bytes de 7 bits; el bit menos significativo
// de cada byte queda libre para la paridad.
static unsigned long des_key(unsigned long key){
  unsigned long k = 0;
  for(int i=0; i<8; ++i){
    key <<= 1;
    k += (key & (0xFEUL << i*8));
  }
  des_setparity((char *)&k);
  return k;
}

static void decrypt(long key, char *ciph, int len){
  unsigned long k = des_key(key);
  ecb_crypt((char *)&k, ciph, len, DES_DECRYPT);
}

static void encrypt(long key, char *ciph, int len){
  unsigned long k = des_key(key);
  ecb_crypt((char *)&k, ciph, len, DES_ENCRYPT);
}

static int tryKey(long key, char *ciph, int len, const char *search){
  char temp[len+1];
  memcpy(temp, ciph, len);
  temp[len]=0;
  decrypt(key, temp, len);
  return strstr(temp, search) != NULL;
}

#endif
