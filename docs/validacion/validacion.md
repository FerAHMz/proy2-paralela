# Parte 2, sección III — Validación: descifrado cruzado local

## Texto elegido

| Equipo elegido | Texto | Palabra objetivo |
|---|---|---|
| Grupo 6 | [`datos/grupo6/cifrado.b64`](../../datos/grupo6/cifrado.b64) (base64 del foro de Canvas, 1928 bytes = 241 bloques DES) | `pan de banano rico y saludable` |

El texto en base64 lo decodificamos con `base64 -D -i cifrado.b64 -o cifrado.bin`. El tamaño es múltiplo de 8 y hay bloques de 8 bytes repetidos, así que es DES en modo ECB, igual que el nuestro. Lo atacamos con el mismo programa de la fase 1 ([`src/bruteforce_texto.c`](../../src/bruteforce_texto.c)) sin modificarlo.

## Ejecución local

Todas las corridas son en una sola máquina (MacBook Pro, Apple Silicon, 12 núcleos):

```bash
cd src
make
mpirun -np 1 ./bruteforce_texto ../datos/grupo6/cifrado.bin "pan de banano rico y saludable"
```

```
Proceso 0 encontró la llave (50001 llaves probadas)
Llave = 50000
Procesos = 1
Tiempo = 0.587673 s

Para este texto de muchas palabras hemos decidio escribir sobre nuestra experiencia durante el curso de computacion paralela y distribuida ...
```

**Llave privada encontrada: `50000`.** El texto plano se recupera completo (346 palabras) y contiene la frase objetivo en el segundo párrafo: *"...vamos a hablar sobre como preparar un pan de banano rico y saludable"*. El texto completo está en [`datos/grupo6/texto_descifrado.txt`](../../datos/grupo6/texto_descifrado.txt).

## Log de tiempo y speedup

Hicimos 5 corridas por cada número de procesos y promediamos. Las corridas individuales están en [`tiempos.csv`](tiempos.csv).

| Procesos | Tiempo promedio (s) | Speedup (T_s / T_p) | Eficiencia (S / p) |
|---|---|---|---|
| 1 | **0.5786** = T_s | 1.000 | 1.000 |
| 2 | 0.5912 | 0.979 | 0.489 |
| 4 | 0.6249 | 0.926 | 0.232 |
| 8 | 0.6585 | 0.879 | 0.110 |

**Tiempo base de referencia: T_s = 0.5786 s** (`-np 1`, promedio de 5 corridas).

Al agregar procesos el tiempo no baja, sube un poco. La llave 50000 es muy pequeña comparada con 2^56, así que siempre cae en el bloque del proceso 0, que la encuentra después de probar 50,001 llaves sin importar cuántos procesos haya. Los demás procesos no aportan nada y solo agregan el costo de arrancarlos y de competir por el CPU. Es el mismo efecto que vimos con nuestra llave en la fase 1, y es importante tenerlo en cuenta en el clúster: con esta llave y la división en bloques contiguos no se va a ver speedup, por más máquinas que agreguemos.
