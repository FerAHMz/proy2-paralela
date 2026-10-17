// Reemplazo de <rpc/des_crypt.h> (glibc) para macOS, donde no existe.
// Misma interfaz y constantes que glibc; la implementación usa OpenSSL (des_compat.c).
#ifndef DES_CRYPT_COMPAT_H
#define DES_CRYPT_COMPAT_H

#define DES_DIRMASK  (1 << 0)
#define DES_ENCRYPT  (0 * DES_DIRMASK)
#define DES_DECRYPT  (1 * DES_DIRMASK)
#define DES_DEVMASK  (1 << 1)
#define DES_HW       (0 * DES_DEVMASK)
#define DES_SW       (1 * DES_DEVMASK)

#define DESERR_NONE       0
#define DESERR_NOHWDEVICE 1
#define DESERR_HWERROR    2
#define DESERR_BADPARAM   3

#define DES_FAILED(err) ((err) > DESERR_NOHWDEVICE)

// Cifra/descifra len bytes (múltiplo de 8) en modo ECB con la llave de 8 bytes.
int ecb_crypt(char *key, char *buf, unsigned len, unsigned mode);
// Ajusta el bit menos significativo de cada byte para dejar paridad impar.
void des_setparity(char *key);

// En macOS <unistd.h> ya declara encrypt(char *, int). Como este header se incluye
// después de unistd.h, se renombra el encrypt() de bruteforce.c para evitar el choque.
#ifdef __APPLE__
#define encrypt bf_encrypt
// En macOS <unistd.h> ya declara encrypt(char *, int). Este header se incluye
// después de unistd.h, así que se renombra el encrypt() de bruteforce.c.
#ifdef __APPLE__
#define encrypt bf_encrypt
#endif

#endif

// En macOS <unistd.h> ya declara encrypt(char *, int). Este header se incluye
// después de unistd.h, así que se renombra el encrypt() de bruteforce.c.
#ifdef __APPLE__
#define encrypt bf_encrypt
#endif

#endif
