// Versión corregida de decrypt/encrypt/tryKey de bruteforce.c.
// Cambios respecto al original:
//  - la máscara es 0xFEL (long): con 0xFE (int) el desplazamiento i*8 >= 32 es
//    comportamiento indefinido y la llave DES queda corrupta.
//  - ecb_crypt recibe len (múltiplo de 8) en vez de 16 fijo, así se cifra todo el texto.
#ifndef DES_UTIL_H
#define DES_UTIL_H

#include <string.h>
#include <rpc/des_crypt.h>

// Reparte los 56 bits de key en 8 bytes de 7 bits; el bit menos significativo
// de cada byte queda libre para la paridad.
static long des_key(long key){
  long k = 0;
  for(int i=0; i<8; ++i){
    key <<= 1;
    k += (key & (0xFEL << i*8));
  }
  des_setparity((char *)&k);
  return k;
}

static void decrypt(long key, char *ciph, int len){
  long k = des_key(key);
  ecb_crypt((char *)&k, ciph, len, DES_DECRYPT);
}

static void encrypt(long key, char *ciph, int len){
  long k = des_key(key);
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
