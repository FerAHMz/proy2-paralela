#!/usr/bin/env python3
"""Mediciones repetidas de la búsqueda MPI; solo usa la biblioteca estándar."""
import argparse
import csv
import hashlib
import json
import os
from pathlib import Path
import platform
import random
import re
import signal
import statistics
import subprocess
import tempfile
import time
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[1]
UPPER = 1 << 56
FRASE = "computación paralela y distribuida"


def ejecutar(command, timeout=300):
    inicio = time.perf_counter()
    with subprocess.Popen(command, cwd=ROOT, stdout=subprocess.PIPE,
                          stderr=subprocess.PIPE, start_new_session=True) as proc:
        try:
            out, err = proc.communicate(timeout=timeout)
        except subprocess.TimeoutExpired:
            os.killpg(proc.pid, signal.SIGKILL)
            proc.communicate()
            raise RuntimeError(f"Tiempo límite excedido: {command}")
        if proc.returncode:
            raise RuntimeError(f"Falló {command}: {err.decode(errors='replace')}")
    return out, err, time.perf_counter() - inicio


def posicion(llave, procesos):
    bloque = UPPER // procesos
    ganador = min(llave // bloque, procesos - 1)
    return ganador, llave - ganador * bloque + 1


def validar(out, llave, procesos, texto):
    """No basta encontrar la frase: comprobar llave, ganador y texto completo."""
    key = re.search(rb"^Llave = (\d+)$", out, re.M)
    np = re.search(rb"^Procesos = (\d+)$", out, re.M)
    winner = re.search(r"^Proceso (\d+) encontró la llave \((\d+) llaves probadas\)$".encode(), out, re.M)
    tiempo = re.search(rb"^Tiempo = ([0-9.]+) s\n\n", out, re.M)
    if not all((key, np, winner, tiempo)):
        raise ValueError("Salida MPI incompleta")
    if int(key[1]) != llave or int(np[1]) != procesos:
        raise ValueError("Llave o número de procesos incorrecto")
    if tuple(map(int, winner.groups())) != posicion(llave, procesos):
        raise ValueError("Ganador o número de intentos incorrecto")
    padded = texto + b" " * (-len(texto) % 8)
    if out[tiempo.end():] != padded + b"\n":
        raise ValueError("El texto recuperado no coincide byte por byte")
    segundos = float(tiempo[1])
    if segundos <= 0:
        raise ValueError("Tiempo no positivo")
    return segundos


def escribir_csv(path, filas):
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(filas[0]))
        writer.writeheader()
        writer.writerows(filas)


def resumir(filas):
    resumen = []
    for key, np in sorted({(r["llave"], r["procesos"]) for r in filas}):
        tiempos = [r["segundos_busqueda"] for r in filas
                   if (r["llave"], r["procesos"]) == (key, np)]
        rank, intentos = posicion(key, np)
        media = statistics.mean(tiempos)
        sd = statistics.stdev(tiempos) if len(tiempos) > 1 else 0
        resumen.append(dict(llave=key, procesos=np, repeticiones=len(tiempos),
                            ganador=rank, intentos_ganador=intentos, media_s=media,
                            desviacion_s=sd, minimo_s=min(tiempos), maximo_s=max(tiempos),
                            cv_porcentaje=100 * sd / media))
    bases = {r["llave"]: r["media_s"] for r in resumen if r["procesos"] == 1}
    for r in resumen:
        speedup = bases.get(r["llave"], 0) / r["media_s"]
        r["speedup"] = speedup if r["llave"] in bases else ""
        r["eficiencia"] = speedup / r["procesos"] if r["llave"] in bases else ""
    return resumen


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--llaves", nargs="+", type=int,
                        default=[50000, 500000, 3141592, (1 << 54) + 50000, (1 << 55) + 50000])
    parser.add_argument("--procesos", nargs="+", type=int, default=[1, 2, 4])
    parser.add_argument("--repeticiones", type=int, default=3)
    parser.add_argument("--max-intentos", type=int, default=4000000)
    parser.add_argument("--timeout", type=float, default=300)
    parser.add_argument("--semilla", type=int, default=23195)
    parser.add_argument("--texto", type=Path, default=ROOT / "datos/texto.txt")
    parser.add_argument("--frase", default=FRASE)
    parser.add_argument("--salida", type=Path, default=ROOT / "bench/resultados")
    args = parser.parse_args()
    if (args.repeticiones < 2 or args.max_intentos < 1 or args.timeout <= 0
            or any(n < 1 or n > UPPER for n in args.procesos)
            or any(k < 0 or k >= UPPER for k in args.llaves)):
        parser.error("Use al menos 2 repeticiones, procesos positivos y llaves en [0, 2^56)")
    texto = args.texto.read_bytes()
    if not args.frase or args.frase.encode() not in texto or b"\0" in texto:
        parser.error("El texto debe contener la frase no vacía y no contener bytes nulos")
    args.salida.mkdir(parents=True, exist_ok=False)
    logs = args.salida / "logs"
    logs.mkdir()
    subprocess.run(["make", "-C", str(ROOT / "src"), "all"], check=True)
    casos, omitidos = [], []
    for key in sorted(set(args.llaves)):
        for np in sorted(set(args.procesos)):
            _, intentos = posicion(key, np)
            if intentos > args.max_intentos:
                omitidos.append(dict(llave=key, procesos=np, intentos_ganador=intentos,
                                     motivo="Supera --max-intentos; no se ejecutó ni se estimó su tiempo"))
            else:
                casos.extend((key, np, r) for r in range(1, args.repeticiones + 1))
    if not casos:
        parser.error("No hay casos ejecutables con --max-intentos")
    random.Random(args.semilla).shuffle(casos)
    metadata = dict(fecha_utc=datetime.now(timezone.utc).isoformat(),
                    sistema=platform.platform(), arquitectura=platform.machine(),
                    cpu_logicas=os.cpu_count(),
                    mpi=ejecutar(["mpirun", "--version"])[0].decode(),
                    compilador=ejecutar(["mpicc", "--version"])[0].decode(),
                    commit=ejecutar(["git", "rev-parse", "HEAD"])[0].decode().strip(),
                    estado_git=ejecutar(["git", "status", "--short"])[0].decode(),
                    sha256={p: hashlib.sha256((ROOT / p).read_bytes()).hexdigest()
                            for p in ["src/bruteforce_texto.c", "src/des_util.h", "src/compat/des_compat.c",
                                      "src/Makefile", "src/bruteforce_texto", "src/cifrar", "bench/medir.py"]},
                    texto_sha256=hashlib.sha256(texto).hexdigest(),
                    palabras=len(texto.decode().split()), bytes_texto=len(texto),
                    frase=args.frase, semilla=args.semilla, repeticiones=args.repeticiones,
                    max_intentos=args.max_intentos, timeout_s=args.timeout,
                    omitidos=omitidos, orden=casos, afinidad="--bind-to none",
                    calentamiento="Una búsqueda con llave 19 por cada cantidad de procesos",
                    estado="en curso")
    if platform.system() == "Darwin":
        metadata["hardware"] = ejecutar(["sysctl", "machdep.cpu.brand_string", "hw.physicalcpu", "hw.memsize"])[0].decode()
    meta_path = args.salida / "entorno.json"
    meta_path.write_text(json.dumps(metadata, ensure_ascii=False, indent=2) + "\n")
    filas = []
    with tempfile.TemporaryDirectory(prefix="des-bench-") as tmp:
        for key in sorted({c[0] for c in casos} | {19}):
            cifrado = Path(tmp) / f"{key}.bin"
            ejecutar([str(ROOT / "src/cifrar"), str(key), str(args.texto.resolve()), str(cifrado)])
        for np in sorted({c[1] for c in casos}):
            command = ["mpirun", "--bind-to", "none", "-np", str(np),
                       str(ROOT / "src/bruteforce_texto"), str(Path(tmp) / "19.bin"), args.frase]
            out, _, _ = ejecutar(command, args.timeout)
            validar(out, 19, np, texto)
        for orden, (key, np, rep) in enumerate(casos, 1):
            command = ["mpirun", "--bind-to", "none", "-np", str(np),
                       str(ROOT / "src/bruteforce_texto"), str(Path(tmp) / f"{key}.bin"), args.frase]
            out, err, pared = ejecutar(command, args.timeout)
            nombre = f"k{key}_np{np}_r{rep}"
            (logs / f"{nombre}.txt").write_bytes(out)
            (logs / f"{nombre}.stderr.txt").write_bytes(err)
            segundos = validar(out, key, np, texto)
            rank, intentos = posicion(key, np)
            filas.append(dict(orden=orden, llave=key, procesos=np, repeticion=rep,
                              ganador=rank, intentos_ganador=intentos,
                              segundos_busqueda=segundos, segundos_comando=pared,
                              cifrado_sha256=hashlib.sha256((Path(tmp) / f"{key}.bin").read_bytes()).hexdigest(),
                              log=f"logs/{nombre}.txt"))
            escribir_csv(args.salida / "mediciones.csv", filas)
            print(f"[{orden}/{len(casos)}] llave={key}, np={np}, repetición={rep}: {segundos:.6f} s", flush=True)
    escribir_csv(args.salida / "resumen.csv", resumir(filas))
    metadata["estado"] = "completo"
    meta_path.write_text(json.dumps(metadata, ensure_ascii=False, indent=2) + "\n")


if __name__ == "__main__":
    main()
