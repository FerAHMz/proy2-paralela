#!/usr/bin/env python3
"""Compone el PDF de las tareas de rendimiento a partir de evidencia del repositorio."""
import csv
import json
from pathlib import Path
from xml.sax.saxutils import escape

import matplotlib
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, PageBreak

from graficar import LABELS

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs/rendimiento"


def main():
    fonts = Path(matplotlib.get_data_path()) / "fonts/ttf"
    pdfmetrics.registerFont(TTFont("DejaVu", str(fonts / "DejaVuSans.ttf")))
    pdfmetrics.registerFont(TTFont("DejaVuBold", str(fonts / "DejaVuSans-Bold.ttf")))
    styles = {
        "titulo": ParagraphStyle("titulo", fontName="DejaVuBold", fontSize=19, leading=23, spaceAfter=12,
                                 textColor=colors.HexColor("#176B87")),
        "seccion": ParagraphStyle("seccion", fontName="DejaVuBold", fontSize=12, leading=16, spaceBefore=9, spaceAfter=6),
        "cuerpo": ParagraphStyle("cuerpo", fontName="DejaVu", fontSize=9.5, leading=14, spaceAfter=8),
        "nota": ParagraphStyle("nota", fontName="DejaVu", fontSize=8, leading=11, spaceAfter=8),
    }
    meta = json.loads((ROOT / "bench/resultados/entorno.json").read_text())
    if meta["estado"] != "completo":
        raise ValueError("No se puede publicar una campaña incompleta")
    with (ROOT / "bench/resultados/resumen.csv").open() as f:
        rows = list(csv.DictReader(f))
    story = []

    def texto(value, estilo="cuerpo"):
        story.append(Paragraph(escape(value), styles[estilo]))

    texto("Búsqueda DES con MPI", "titulo")
    texto("Felipe Aguilar · FelipeAP04 | Proyecto 2 · Tareas 6 y 7", "nota")
    texto("Mediciones y método", "seccion")
    texto("Usamos el texto real de 352 palabras del grupo (2162 bytes, 2168 con relleno). "
          "La frase de búsqueda fue «computación paralela y distribuida». Probamos cinco llaves "
          "con 1, 2 y 4 procesos: 36 ejecuciones válidas, tres por combinación viable. "
          "Cada ejecución recuperó la llave esperada y el texto completo, verificado byte por byte.")
    texto(f"Equipo: Apple M4 Pro, 14 núcleos y 24 GiB de RAM; {meta['sistema']}. "
          "Open MPI 5.0.11, Apple clang 21.0.0 y optimización -O2. Todos los procesos se ejecutaron "
          "en una máquina, sin afinidad fija (--bind-to none). Inicio UTC: " + meta["fecha_utc"].split(".")[0] + ".")
    texto("El orden se aleatorizó con semilla 23195, con un calentamiento por cantidad de procesos. "
          "MPI_Wtime mide desde la barrera inicial hasta que el proceso 0 recibe la llave; excluye "
          "arranque MPI, lectura, descifrado final y finalización. No es el tiempo máximo de los procesos. "
          "Se registró aparte la duración externa de cada comando.")
    texto("Promedios de búsqueda", "seccion")
    table = [["Llave", "np", "Ganador", "Media (s)", "DE (s)", "Speedup", "Eficiencia"]]
    for r in rows:
        table.append([LABELS[int(r["llave"])], r["procesos"], r["ganador"],
                      f'{float(r["media_s"]):.4f}', f'{float(r["desviacion_s"]):.4f}',
                      f'{float(r["speedup"]):.3f}' if r["speedup"] else "N/D",
                      f'{float(r["eficiencia"]) * 100:.1f} %' if r["eficiencia"] else "N/D"])
    tabla = Table(table, colWidths=[80, 30, 58, 72, 72, 66, 66], repeatRows=1)
    tabla.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (-1, -1), "DejaVu"),
        ("FONTSIZE", (0, 0), (-1, -1), 8.5),
        ("FONTNAME", (0, 0), (-1, 0), "DejaVuBold"),
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#176B87")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.HexColor("#F0F5F7"), colors.white]),
        ("ALIGN", (1, 0), (-1, -1), "RIGHT"),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
    ]))
    story.extend([tabla, Spacer(1, 10)])
    texto("DE: desviación estándar muestral; tres repeticiones por fila. "
          "Speedup = media T₁ / media Tₚ; eficiencia = speedup / p. "
          "A = 2⁵⁴ + 50000; B = 2⁵⁵ + 50000. N/D: no se ejecutó la base de un proceso.", "nota")
    texto("Se omitieron A con 1 y 2 procesos, y B con 1 proceso: su ganador necesitaría más de cuatro "
          "millones de intentos. Este filtro no modifica el espacio de 56 bits del programa. "
          "No se asignaron tiempos ni speedups a los casos omitidos.", "nota")
    story.append(PageBreak())
    texto("Tiempos y speedup", "titulo")
    story.append(Image(str(DOCS / "tiempos.png"), width=510, height=510 * 4.1 / 9))
    texto("Figura 1. Promedio ± una desviación estándar muestral; no son intervalos de confianza. "
          "La izquierda usa escala logarítmica y la derecha lineal. A = 18014398509531984; "
          "B = 36028797019013968. Los puntos ausentes son casos omitidos, no tiempos cero.", "nota")
    story.append(Spacer(1, 12))
    story.append(Image(str(DOCS / "speedup.png"), width=510, height=510 * 4.1 / 9))
    texto("Figura 2. Cociente de promedios para una misma llave y el mismo texto. "
          "La referencia ideal S = p no representa una medición. Las llaves altas no aparecen "
          "porque no tienen una base medida con un proceso.", "nota")
    story.append(PageBreak())
    for bloque in (DOCS / "analisis.md").read_text().strip().split("\n\n"):
        if bloque.startswith("# "):
            texto(bloque[2:], "titulo")
        elif bloque.startswith("## "):
            texto(bloque[3:], "seccion")
        else:
            texto(" ".join(bloque.splitlines()))

    def footer(canvas, doc):
        canvas.setFont("DejaVu", 8)
        canvas.setFillColor(colors.HexColor("#555555"))
        canvas.drawString(48, 27, "Proyecto 2 · Computación paralela y distribuida")
        canvas.drawRightString(564, 27, str(doc.page))

    SimpleDocTemplate(str(DOCS / "informe_felipe.pdf"), pagesize=letter,
                      leftMargin=48, rightMargin=48, topMargin=40, bottomMargin=43,
                      title="Rendimiento de la búsqueda DES con MPI", author="Felipe Aguilar",
                      subject="Tareas 6 y 7: mediciones e impacto de la llave").build(
                          story, onFirstPage=footer, onLaterPages=footer)


if __name__ == "__main__":
    main()
