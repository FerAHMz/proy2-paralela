# Tarea 4 — Texto de 350 palabras cifrado con llave privada

## Texto y frase clave

- Texto plano: [`datos/texto.txt`](../../datos/texto.txt), **352 palabras** (`wc -w`), 2162 bytes.
- Frase clave de búsqueda: **`computación paralela y distribuida`**. Aparece una sola vez en el texto, en el segundo párrafo.
- Llave privada: **`3141592`**.
- Texto cifrado: [`datos/texto_cifrado.bin`](../../datos/texto_cifrado.bin), 2168 bytes.

## Cómo se cifró

[`src/cifrar.c`](../../src/cifrar.c) lee el archivo, lo rellena con espacios hasta un múltiplo de 8 bytes (2162 → 2168) y llama a `encrypt` de [`src/des_util.h`](../../src/des_util.h). Esta es la misma función del `bruteforce.c` original, con las dos correcciones descritas en [compilacion.md](compilacion.md), así que cifra los 271 bloques en modo ECB. Rellenamos con espacios en lugar de ceros para que el texto descifrado no tenga un `\0` antes del final, porque eso cortaría la búsqueda de `strstr`.

```bash
cd src
make
./cifrar 3141592 ../datos/texto.txt ../datos/texto_cifrado.bin
```

Primeros bytes del cifrado (`xxd`):

```
00000000: 4bcb 99ac 9452 16c4 b82e d998 15b6 0abc  K....R..........
00000010: 0eee 0710 1201 dcb2 bb10 8c0a 1c8c 744b  ..............tK
```

## Verificación

```
$ mpirun -np 4 ./bruteforce_texto ../datos/texto_cifrado.bin "computación paralela y distribuida"
Proceso 0 encontró la llave (3141593 llaves probadas)
Llave = 3141592
Procesos = 4
Tiempo = 45.409920 s

La computación paralela dejó de ser un tema exclusivo de ...
```

Con `-np 1` el tiempo fue de 43.03 s, prácticamente igual. Como la llave es pequeña, cae en el bloque del proceso 0 y los demás procesos no aportan nada. El análisis de este efecto con distintas llaves corresponde a las tareas 6 y 7.

Para probar otras llaves basta con volver a cifrar el mismo texto con `./cifrar <llave> ../datos/texto.txt <salida.bin>`.
