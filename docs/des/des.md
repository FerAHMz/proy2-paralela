# Tarea 1 — Investigación: DES (Data Encryption Standard)

## 1. ¿Qué es DES?

DES es un algoritmo de **cifrado simétrico por bloques** publicado por el NIST (antes NBS) en 1977 como estándar FIPS 46, basado en el cifrado *Lucifer* de IBM. Simétrico significa que **la misma llave sirve para cifrar y para descifrar**.

| Característica | Valor |
|---|---|
| Tipo | Cifrado por bloques, red de Feistel |
| Tamaño de bloque | 64 bits (8 bytes) |
| Tamaño de llave | 64 bits, de los cuales **56 son efectivos** (8 son de paridad) |
| Número de rondas | 16 |
| Tamaño de subllave por ronda | 48 bits |
| Espacio de llaves | 2^56 ≈ 7.2 × 10^16 llaves posibles |

## 2. Estructura general (red de Feistel)

Una red de Feistel divide el bloque en dos mitades y en cada ronda transforma solo una de ellas usando una función `f` y una subllave. La propiedad clave es que **descifrar usa exactamente el mismo circuito que cifrar**, solo invirtiendo el orden de las subllaves; la función `f` no necesita ser invertible.

## 3. Pasos para cifrar un bloque de 64 bits

1. **Permutación inicial (IP).** Los 64 bits del bloque de texto plano se reordenan según una tabla fija.
2. **División.** El resultado se separa en dos mitades de 32 bits: `L0` (izquierda) y `R0` (derecha).
3. **16 rondas.** Para cada ronda `i = 1 … 16`:
   - `Li = R(i-1)`
   - `Ri = L(i-1) XOR f(R(i-1), Ki)`
4. **Intercambio final.** Tras la ronda 16 se intercambian las mitades: se forma `R16 ‖ L16`.
5. **Permutación final (IP⁻¹).** Se aplica la inversa de la permutación inicial. El resultado es el bloque cifrado de 64 bits.

### 3.1 La función de ronda `f(R, K)`

1. **Expansión (E):** los 32 bits de `R` se expanden a 48 bits duplicando algunos bits según la tabla E.
2. **Mezcla con la llave:** `E(R) XOR Ki` (48 bits).
3. **Sustitución (S-boxes):** los 48 bits se parten en 8 grupos de 6 bits; cada grupo entra a una caja S distinta (S1…S8) que devuelve 4 bits. Los bits 1 y 6 eligen la fila y los bits 2–5 la columna. Salida: 32 bits. **Es el único paso no lineal de DES** y es lo que le da su seguridad.
4. **Permutación (P):** los 32 bits se reordenan con la tabla P.

### 3.2 Generación de subllaves (key schedule)

1. **PC-1:** de la llave de 64 bits se descartan los 8 bits de paridad (uno por byte) y se permutan los 56 restantes.
2. Se dividen en dos mitades de 28 bits: `C0` y `D0`.
3. Para cada ronda `i`, ambas mitades se **rotan a la izquierda** 1 posición (rondas 1, 2, 9 y 16) o 2 posiciones (el resto).
4. **PC-2:** de los 56 bits `Ci ‖ Di` se seleccionan y permutan 48 bits, que forman la subllave `Ki`.

## 4. Pasos para descifrar

El descifrado es **el mismo algoritmo** aplicado al texto cifrado, con las subllaves en orden inverso: `K16, K15, …, K1`.

1. IP sobre el bloque cifrado.
2. 16 rondas de Feistel usando `K16` en la primera ronda y `K1` en la última.
3. Intercambio de mitades y IP⁻¹.
4. Se obtiene el bloque de texto plano original.

Si la llave usada para descifrar **no** es la correcta, el resultado es basura binaria; no hay error explícito. Por eso el programa de fuerza bruta valida cada intento buscando una **frase clave conocida** dentro del texto descifrado.

## 5. Textos de más de 8 bytes: modos de operación y padding

DES solo cifra bloques de 8 bytes. Para un texto más largo:

- **Padding:** se rellena el texto hasta un múltiplo de 8 bytes.
- **Modo ECB (Electronic Codebook):** cada bloque de 8 bytes se cifra de forma independiente con la misma llave. Es el modo más simple; su debilidad es que bloques de texto plano iguales producen bloques cifrados iguales.
- **Modo CBC (Cipher Block Chaining):** cada bloque se combina (XOR) con el bloque cifrado anterior antes de cifrarse, usando un vector de inicialización (IV) para el primero. Oculta patrones.

## 6. Seguridad y relación con el proyecto

- 56 bits efectivos son **pocos** para el hardware moderno. En 1998 la máquina *Deep Crack* de la EFF encontró una llave DES por fuerza bruta en 56 horas, y en 1999 se bajó a unas 22 horas. Por eso DES fue reemplazado por **3DES** y luego por **AES** (2001).
- Como no hay atajo práctico, la forma de romperlo es **probar llaves**: en el peor caso hay que recorrer las 2^56 llaves, y cada intento implica descifrar el texto completo y buscar la frase clave.
- Ese recorrido es **embarazosamente paralelo**: cada llave se prueba de forma independiente. Con MPI el rango `[0, 2^56)` se divide entre los procesos, y cada uno recorre su propio subrango. **La posición de la llave correcta dentro de esos subrangos** determina qué tan rápido se encuentra, que es lo que se analiza en las tareas 6 y 7.

## Referencias

- National Bureau of Standards. *FIPS PUB 46: Data Encryption Standard*. 1977 (revisado como FIPS 46-3, 1999).
- Stallings, W. *Cryptography and Network Security: Principles and Practice*, cap. 4 "Block Ciphers and the Data Encryption Standard".
- Electronic Frontier Foundation. *Cracking DES: Secrets of Encryption Research, Wiretap Politics & Chip Design*. O'Reilly, 1998.
