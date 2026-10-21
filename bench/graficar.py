#!/usr/bin/env python3
"""Genera las figuras y la tabla del informe a partir de promedios medidos."""
import argparse
import csv
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
LABELS = {50000: "50 000", 500000: "500 000", 3141592: "3 141 592",
          (1 << 54) + 50000: "A", (1 << 55) + 50000: "B"}
COLORS = ["#176B87", "#C15C22", "#6D4592", "#36835C", "#B34367"]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--resumen", type=Path, default=ROOT / "bench/resultados/resumen.csv")
    parser.add_argument("--salida", type=Path, default=ROOT / "docs/rendimiento")
    args = parser.parse_args()
    with args.resumen.open() as f:
        rows = list(csv.DictReader(f))
    keys = sorted({int(r["llave"]) for r in rows})
    repeticiones = ", ".join(sorted({r["repeticiones"] for r in rows}))
    plt.rcParams.update({"font.size": 10, "axes.spines.top": False,
                         "axes.spines.right": False, "axes.titleweight": "bold"})
    args.salida.mkdir(parents=True, exist_ok=True)
    fig, axes = plt.subplots(1, 2, figsize=(9, 4.1), layout="constrained")
    for i, key in enumerate(keys):
        data = sorted((r for r in rows if int(r["llave"]) == key), key=lambda r: int(r["procesos"]))
        ax = axes[0 if all(r["speedup"] for r in data) else 1]
        ax.errorbar([int(r["procesos"]) for r in data], [float(r["media_s"]) for r in data],
                    yerr=[float(r["desviacion_s"]) for r in data], fmt=["o-", "s-", "^-", "D-", "o-"][i % 5],
                    markersize=9 if i == 3 else 5, markerfacecolor="none", capsize=4,
                    color=COLORS[i % len(COLORS)], label=LABELS.get(key, str(key)))
    axes[0].set_title("Llaves pequeñas")
    axes[0].set_yscale("log")
    axes[0].set_ylabel("Tiempo de búsqueda (s, escala log)")
    axes[1].set_title("Llaves altas cerca de un inicio")
    axes[1].set_ylabel("Tiempo de búsqueda (s)")
    altas = [float(r["media_s"]) + float(r["desviacion_s"]) for r in rows if not r["speedup"]]
    axes[1].set_ylim(0, max(altas, default=1) * 1.2)
    for ax in axes:
        ax.set_xticks([1, 2, 4])
        ax.set_xlim(0.7, 4.3)
        ax.set_xlabel("Procesos MPI")
        ax.grid(axis="y", alpha=0.25)
        ax.legend(fontsize=9, loc="upper center", bbox_to_anchor=(0.5, -0.22), ncol=3)
    fig.suptitle(f"Promedio ± desviación estándar muestral (n = {repeticiones})")
    fig.savefig(args.salida / "tiempos.png", dpi=180)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(9, 4.1), layout="constrained")
    for i, key in enumerate(keys):
        data = sorted((r for r in rows if int(r["llave"]) == key and r["speedup"]),
                      key=lambda r: int(r["procesos"]))
        if data:
            ax.plot([int(r["procesos"]) for r in data], [float(r["speedup"]) for r in data],
                    ["o-", "s--", "^:"][i % 3], markersize=[6, 10, 5][i % 3], markerfacecolor="none",
                    color=COLORS[i % len(COLORS)], label=LABELS.get(key, str(key)))
    ax.plot([1, 2, 4], [1, 2, 4], "--", color="#888888", label="Referencia ideal S = p")
    ax.axhline(1, color="#aaaaaa", linewidth=0.8)
    ax.set(xticks=[1, 2, 4], xlabel="Procesos MPI", ylabel="Speedup: promedio T₁ / promedio Tₚ",
           title="Speedup con la misma llave y el mismo texto", ylim=(0, 4.3))
    ax.grid(axis="y", alpha=0.25)
    ax.legend(title="Llave / referencia", loc="upper left", ncol=2)
    fig.savefig(args.salida / "speedup.png", dpi=180)
    plt.close(fig)

    table = ["# Resultados medidos", "", f"Repeticiones por combinación: {repeticiones}. DE: desviación estándar muestral.", "",
             "| Llave | np | Ganador | Intentos del ganador | Media (s) | DE (s) | Speedup | Eficiencia |",
             "|---|---:|---:|---:|---:|---:|---:|---:|"]
    for r in rows:
        speedup = f'{float(r["speedup"]):.3f}' if r["speedup"] else "N/D"
        eficiencia = f'{100 * float(r["eficiencia"]):.1f} %' if r["eficiencia"] else "N/D"
        table.append(f'| {LABELS.get(int(r["llave"]), r["llave"])} | {r["procesos"]} | {r["ganador"]} | '
                     f'{int(r["intentos_ganador"]):,} | {float(r["media_s"]):.4f} | '
                     f'{float(r["desviacion_s"]):.4f} | {speedup} | {eficiencia} |')
    table += ["", "A = 2^54 + 50000 = 18014398509531984; B = 2^55 + 50000 = 36028797019013968.",
              "N/D: no se ejecutó la base con un proceso; no corresponde calcular speedup ni eficiencia.", "",
              "![Tiempos de búsqueda](tiempos.png)", "",
              "En la izquierda el eje vertical es logarítmico; en la derecha es lineal.",
              "Los puntos ausentes no representan tiempo cero: son combinaciones omitidas.", "",
              "![Speedup por llave](speedup.png)", "",
              "El speedup es el cociente de promedios, no el promedio de cocientes. La línea ideal es solo una referencia.",
              "Las barras de tiempos muestran dispersión entre repeticiones, no intervalos de confianza.", ""]
    (args.salida / "resultados.md").write_text("\n".join(table), encoding="utf-8")


if __name__ == "__main__":
    main()
