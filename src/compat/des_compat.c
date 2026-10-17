// Implementación de ecb_crypt y des_setparity sobre OpenSSL.
// Se compila aparte porque openssl/des.h define DES_ENCRYPT/DES_DECRYPT con otros valores.
#define OPENSSL_SUPPRESS_DEPRECATED
#include <openssl/des.h>

#define COMPAT_DES_DECRYPT 1
#define COMPAT_BADPARAM    3

int ecb_crypt(char *key, char *buf, unsigned len, unsigned mode){
  if(len % 8 != 0) return COMPAT_BADPARAM;
  DES_key_schedule ks;
  DES_set_key_unchecked((const_DES_cblock *)key, &ks);
  int enc = (mode & COMPAT_DES_DECRYPT) ? DES_DECRYPT : DES_ENCRYPT;
  for(unsigned i = 0; i < len; i += 8){
    DES_ecb_encrypt((const_DES_cblock *)(buf + i), (DES_cblock *)(buf + i), &ks, enc);
  }
  return 0;
}

void des_setparity(char *key){
  DES_set_odd_parity((DES_cblock *)key);
}
