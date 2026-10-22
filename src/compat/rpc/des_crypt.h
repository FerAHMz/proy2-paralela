// Reemplazo de <rpc/des_crypt.h> para plataformas donde no está disponible
// la implementación DES de Sun RPC: macOS no trae el header, y en Ubuntu 22.04
// libtirpc trae el header pero ya no exporta ecb_crypt/des_setparity. En ambos
// casos la implementación la provee des_compat.c con OpenSSL.
// Misma interfaz y constantes que la versión histórica de glibc.
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

// Tanto <unistd.h> de macOS como el de glibc declaran encrypt(char *, int),
// que choca con el encrypt() propio de bruteforce.c/cifrar.c. Como este header
// se incluye después de unistd.h, renombramos el encrypt() del proyecto.
#define encrypt bf_encrypt

// Cifra/descifra len bytes (múltiplo de 8) en modo ECB con la llave de 8 bytes.
int ecb_crypt(char *key, char *buf, unsigned len, unsigned mode);
// Ajusta el bit menos significativo de cada byte para dejar paridad impar.
void des_setparity(char *key);

#endif
