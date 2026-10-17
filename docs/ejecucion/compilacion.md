# Tarea 3 — Compilación y ejecución de `bruteforce.c`

El programa original del catedrático está en [`src/bruteforce.c`](../../src/bruteforce.c), sin modificaciones.

## Compilación

En Linux, `<rpc/des_crypt.h>` viene en glibc (o en `libtirpc` en distribuciones recientes), así que basta con:

```bash
mpicc bruteforce.c -o bruteforce
```

En macOS ese header no existe. Para no tocar el código original agregamos [`src/compat/`](../../src/compat/): un `rpc/des_crypt.h` con la misma interfaz que glibc (`ecb_crypt`, `des_setparity`, `DES_ENCRYPT`, `DES_DECRYPT`) implementado con OpenSSL. El header además renombra `encrypt`, porque en macOS `<unistd.h>` ya declara una función con ese nombre. El [`Makefile`](../../src/Makefile) detecta el sistema operativo y agrega esto solo en macOS:

```bash
cd src
make bruteforce
mpirun -np 4 ./bruteforce
```

Requisitos en macOS: `brew install open-mpi openssl@3`.

## Ejecución

```
$ mpirun -np 4 ./bruteforce
Process 2 lower 36028797018963968 upper 54043195528445951
Process 0 lower 0 upper 18014398509481983
Process 1 lower 18014398509481984 upper 36028797018963967
Process 3 lower 54043195528445952 upper 72057594037927936
```

Cada proceso imprime su rango de llaves, pero el programa **nunca termina**. Lo detuvimos después de varios minutos. Esto llama la atención porque la llave usada (`the_key = 18014398509481984 = 2^54`) es justo el límite inferior del proceso 1 cuando corremos con 4 procesos, así que debería encontrarla en el primer intento.

Probando `tryKey` por separado encontramos tres errores en el código:

1. **La frase de búsqueda nunca aparece en el texto.** Se busca `" los mismos del proyecto 1 "` (con espacios), pero en el texto la frase está entre paréntesis: `"(los mismos del proyecto 1)"`. `strstr` nunca hace match, ni siquiera con la llave correcta.
2. **La conversión de la llave tiene comportamiento indefinido.** En `k += (key & (0xFE << i*8))` la constante `0xFE` es `int` (32 bits). Para `i = 3` el resultado es negativo y para `i >= 4` el desplazamiento es de 32 bits o más, lo cual no está definido en C. Al compilar con `-O2`, clang termina generando **la misma llave DES para cualquier valor de `key`** (`0x1fc9b7a60`). Con `-O0` el resultado es otro. La corrección es usar `0xFEL`.
3. **Solo se cifran 16 bytes.** `ecb_crypt` recibe `16` fijo en lugar de `len`, por lo que solo se cifran los primeros dos bloques. El resto del texto queda en claro dentro del "cifrado".

Además, `ciphlen = strlen(eltexto)` no es múltiplo de 8, que es lo que requiere DES en modo ECB.

## Versión corregida

Para las mediciones usamos [`src/bruteforce_texto.c`](../../src/bruteforce_texto.c), que conserva la misma estrategia de distribución del original (rango `[0, 2^56)` dividido en `N` bloques contiguos, aviso con `MPI_Send` e `MPI_Irecv`/`MPI_Test`) pero:

- usa las funciones corregidas de [`src/des_util.h`](../../src/des_util.h) (`0xFEL` y `len` en `ecb_crypt`),
- lee el texto cifrado de un archivo y recibe la frase clave como argumento,
- mide el tiempo de búsqueda con `MPI_Wtime` (entre un `MPI_Barrier` inicial y el momento en que el proceso 0 recibe la llave).

```bash
make
mpirun -np 4 ./bruteforce_texto ../datos/texto_cifrado.bin "computación paralela y distribuida"
```
