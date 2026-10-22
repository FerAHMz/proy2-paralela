# Proyecto 2 — Búsqueda de llaves DES con MPI

CC3069 Computación Paralela y Distribuida — Universidad del Valle de Guatemala.

Búsqueda por fuerza bruta de la llave privada DES con la que se cifró un texto, repartiendo el espacio de 2^56 llaves entre procesos MPI, y análisis de cómo la llave elegida afecta el tiempo y el speedup.

## Integrantes

| Integrante | Carné | Tareas |
|---|---|---|
| Fernando Andree Hernández Martínez | 23645 | 1–2: investigación de DES, diagrama de flujo e integración del informe |
| Fernando José Rueda Rodas | 23748 | 3–5: compilación, texto cifrado y diagramas de las funciones |
| Jorge Luis Felipe Aguilar | 23195 | 6–7: mediciones de tiempo y análisis del impacto de la llave |

## Contenido por tarea

1. [Investigación de DES](docs/des/des.md)
2. [Diagrama de flujo de DES](docs/des/diagrama.md)
3. [Compilación y ejecución de `bruteforce.c`](docs/ejecucion/compilacion.md)
4. [Texto de 352 palabras y su cifrado](docs/ejecucion/texto_cifrado.md)
5. Funciones del programa: [`encrypt`/`decrypt` y `tryKey`](docs/funciones/cifrado_trykey.md), [`memcpy` y `strstr`](docs/funciones/memcpy_strstr.md)
6. [Mediciones: tabla y gráficas](docs/rendimiento/resultados.md), con [metodología y reproducción](bench/README.md)
7. [Análisis del impacto de la llave](docs/rendimiento/analisis.md)

## Parte 2 — Clúster físico con Docker

- [Validación cruzada local (texto del grupo 6)](docs/validacion/validacion.md)
- [Entorno Docker, tabla de validaciones y despliegue del clúster](docs/cluster/docker.md)
- [Troubleshooting: Docker Desktop en macOS no expone el contenedor en la LAN](docs/cluster/limitacion_docker_mac.md)

## Estructura

```
src/      bruteforce.c original, versión corregida (bruteforce_texto.c, des_util.h), cifrar.c y Makefile
datos/    texto plano y texto cifrado
bench/    script de mediciones, resultados (CSV, logs) y generación de gráficas
docs/     documentación de cada tarea
```

## Uso rápido

```bash
cd src
make
./cifrar 3141592 ../datos/texto.txt ../datos/texto_cifrado.bin
mpirun -np 4 ./bruteforce_texto ../datos/texto_cifrado.bin "computación paralela y distribuida"
```

En macOS se necesita `brew install open-mpi openssl@3`. Ver [compilacion.md](docs/ejecucion/compilacion.md).
