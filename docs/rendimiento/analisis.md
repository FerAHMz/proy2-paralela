# Impacto de la llave

## La posición determina los intentos

El programa divide las 2⁵⁶ llaves en bloques contiguos. El tamaño base es la división
entera del espacio entre la cantidad de procesos; el último recibe el residuo.
Cada proceso recorre su bloque en orden ascendente. Los intentos del ganador son
la llave menos el inicio de su bloque, más uno. Por eso importa su posición dentro
del bloque, no solamente el valor numérico de la llave.

Las llaves 50000, 500000 y 3141592 pertenecen al proceso 0 con 1, 2 y 4 procesos.
Este prueba respectivamente 50001, 500001 y 3141593 candidatos en cualquiera de
esas configuraciones. Los demás trabajan, pero no reducen ese recorrido.
Con la llave original 3141592, el promedio fue 45.3373 s con un proceso y
46.1428 s con cuatro: speedup 0.983 y eficiencia 24.6 %. No observamos aceleración.

## Una llave alta puede encontrarse antes

A = 2⁵⁴ + 50000 cae en el bloque del proceso 1 con cuatro procesos: requiere
50001 intentos y promedia 0.7360 s. B = 2⁵⁵ + 50000 requiere también 50001 intentos,
pero la encuentra el proceso 1 con dos procesos y el proceso 2 con cuatro;
sus promedios son 0.7318 y 0.7337 s. Son llaves mucho mayores que 3141592,
pero están cerca del inicio de un bloque. Cerca del final habría que recorrer
casi todo ese bloque. Cambiar la cantidad de procesos cambia estos límites.

No medimos A ni B con un proceso: exigirían más de 18 mil billones de intentos.
Tampoco medimos A con dos procesos. Los tiempos paralelos sí son reales,
pero no permiten reportar un speedup sin una base equivalente medida.

## El speedup aparente puede engañar

Elegir llaves junto al inicio de un bloque favorece al recorrido paralelo frente
al secuencial. Un speedup incluso superior al número de procesos podría deberse
a ese cambio del orden de búsqueda, no a una mayor capacidad de cómputo.
Nuestra campaña muestra esa dependencia; no demuestra aceleración superlineal.

La llave 50000 produjo un speedup de 1.099 con cuatro procesos, aunque el ganador
hizo los mismos intentos. La base tuvo una muestra de 0.977363 s frente a otras
de 0.721127 y 0.722594 s: su coeficiente de variación fue 18.28 %.
Conservamos las tres muestras. No atribuimos esa aparente mejora a la distribución;
no registramos información suficiente para explicar la corrida lenta.

## Alcance y conclusión

Tres repeticiones describen esta campaña, no prueban significancia estadística.
Las llaves se eligieron para contrastar posiciones, no como una muestra uniforme.
No medimos red entre máquinas ni intentos totales: el contador corresponde solo
al ganador. La planificación del sistema, la frecuencia de CPU y la comunicación
también pueden afectar el tiempo; no aislamos sus aportes.

Antes de medir corregimos desplazamientos con signo, un límite de bloque y la
finalización de recepciones. El cifrado original se conservó byte por byte;
siete llaves se contrastaron con OpenSSL y el cifrado pasó el sanitizador UBSan.
Concluimos que este reparto no acelera las llaves pequeñas evaluadas. Un reparto
cíclico sería una alternativa para distribuir mejor sus candidatos, pero no se
implementó ni se midió aquí.

Evidencia reproducible: bench/resultados/mediciones.csv, resumen.csv, entorno.json
y logs/. El procedimiento está en bench/README.md; el código medido está en
src/bruteforce_texto.c y src/des_util.h.
