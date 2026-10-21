# Mediciones de Felipe

Desde la raíz del repositorio, con Python 3, Open MPI, `make` y las dependencias de `src/Makefile`:

```bash
python3 -B -m unittest discover -s bench -p 'test_*.py'
python3 -B bench/medir.py
```

El segundo comando genera `bench/resultados/` y no sobrescribe carpetas existentes.
Para repetir la campaña, usar `--salida /ruta/a/una/carpeta/nueva`.
El script compila con `make`, cifra el texto real con cada llave en archivos temporales
y ejecuta los casos de forma secuencial, en orden aleatorio reproducible (semilla 23195).
Hace un calentamiento con llave 19 por cantidad de procesos; no lo incluye en el promedio.
No modifica `datos/texto_cifrado.bin`. La salida descifrada se valida byte por byte,
incluyendo el relleno de espacios, además de verificar llave, proceso ganador e intentos.

## Diseño de la campaña

- Texto: `datos/texto.txt`, 352 palabras, 2162 bytes; 2168 bytes al rellenarlo para DES.
- Frase: `computación paralela y distribuida`.
- Llaves: 50000, 500000, 3141592, 18014398509531984 (2^54 + 50000)
  y 36028797019013968 (2^55 + 50000).
- Procesos: 1, 2 y 4; tres repeticiones por combinación viable.
- `--max-intentos 4000000` excluye combinaciones cuyo ganador necesitaría demasiados
  intentos. **No reduce el espacio de búsqueda de 56 bits ni detiene el programa C**:
  filtra casos antes de ejecutarlos. Los casos omitidos quedan en `entorno.json`.
- `--timeout 300` limita cada comando a 300 segundos; un fallo interrumpe la campaña,
  conserva mediciones previas y no genera un resumen final como si hubiera terminado.
- `mpirun --bind-to none`: sin afinidad fija, todos los procesos en esta máquina.

Se ejecutan 36 mediciones: 27 para las tres llaves pequeñas y nueve para las altas.
Las combinaciones inviables son ambas llaves altas con un proceso y 2^54 + 50000 con dos.
No se inventan tiempos ni speedups para esas combinaciones.

## Archivos y significado

- `mediciones.csv`: muestras individuales, duración externa del comando, hash del cifrado y log.
- `resumen.csv`: promedio, desviación estándar muestral, mínimo, máximo y coeficiente de variación.
- `entorno.json`: versiones, hardware, hashes, orden de ejecución y casos omitidos.
- `logs/`: salida y errores originales de cada ejecución.

El tiempo principal proviene de `MPI_Wtime`: inicia después de `MPI_Barrier` y termina
cuando el proceso 0 recibe la llave. Incluye la búsqueda y la notificación al proceso 0;
no incluye arranque de MPI, lectura del archivo, descifrado final ni `MPI_Finalize`.
No es el máximo tiempo de todos los procesos. `segundos_comando` registra por separado
la duración externa de `mpirun`, incluyendo esos costos, pero no el cifrado previo.

Speedup = promedio con un proceso / promedio con p procesos, siempre para la misma llave.
Eficiencia = speedup / p. Si falta la base de un proceso, ambos campos quedan vacíos.
Los intentos corresponden solo al ganador; no son el trabajo total de todos los procesos.

## Ajustes necesarios para medir

Se conserva `src/bruteforce.c` original. En la versión para archivos, la conversión DES
usa `unsigned long`: `long` con signo todavía desbordaba al desplazar llaves altas,
incluso con la máscara `0xFEL`. También se corrige el límite exclusivo de cada bloque
para no saltarse su última llave y se completan las recepciones MPI en todos los procesos.
No cambia la estrategia de bloques contiguos. Esta implementación requiere `long` de
64 bits y usa el orden de bytes de la máquina; no se ha validado en un clúster heterogéneo.
Se presupone una llave recuperable y una frase única: el programa no resuelve el caso
de agotamiento sin coincidencia y una frase corta puede dar falsos positivos.

Para pruebas rápidas o un texto distinto:

```bash
python3 -B bench/medir.py --llaves 19 127 --procesos 1 2 4 \
  --repeticiones 2 --salida /tmp/des-prueba
python3 -B bench/medir.py --texto otro.txt --frase 'frase presente' \
  --llaves 1000 10000 --salida /tmp/des-otro-texto
```
