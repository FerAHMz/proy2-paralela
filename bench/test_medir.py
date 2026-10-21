"""Regresión de cifrado/búsqueda real y del resumen público del benchmark."""
import csv
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


class MedicionesTest(unittest.TestCase):
    def test_matriz_y_recuperacion_del_texto(self):
        with tempfile.TemporaryDirectory() as tmp:
            salida = Path(tmp) / "resultados"
            subprocess.run([
                sys.executable, str(ROOT / "bench/medir.py"),
                "--llaves", "0", "19", str((1 << 54) + 19),
                "--procesos", "1", "4", "--repeticiones", "2",
                "--max-intentos", "100", "--salida", str(salida),
            ], check=True, timeout=90)
            meta = json.loads((salida / "entorno.json").read_text())
            self.assertEqual(meta["estado"], "completo")
            self.assertEqual(len(meta["omitidos"]), 1)
            self.assertEqual(meta["omitidos"][0]["procesos"], 1)
            with (salida / "mediciones.csv").open() as f:
                mediciones = list(csv.DictReader(f))
            with (salida / "resumen.csv").open() as f:
                resumen = list(csv.DictReader(f))
            self.assertEqual(len(mediciones), 10)
            self.assertEqual(len(resumen), 5)
            texto = (ROOT / "datos/texto.txt").read_bytes()
            esperado = texto + b" " * (-len(texto) % 8) + b"\n"
            for row in mediciones:
                self.assertTrue((salida / row["log"]).read_bytes().endswith(esperado))
                self.assertEqual(int(row["intentos_ganador"]), 1 if row["llave"] == "0" else 20)
                self.assertEqual(int(row["ganador"]), 1 if int(row["llave"]) > 19 else 0)
            for row in resumen:
                tiempos = [float(m["segundos_busqueda"]) for m in mediciones
                           if (m["llave"], m["procesos"]) == (row["llave"], row["procesos"])]
                self.assertAlmostEqual(float(row["media_s"]), sum(tiempos) / 2)
                self.assertAlmostEqual(float(row["desviacion_s"]), abs(tiempos[0] - tiempos[1]) / 2**0.5)
                if int(row["llave"]) > 19:
                    self.assertEqual(row["speedup"], "")
                    self.assertEqual(row["eficiencia"], "")
                else:
                    base = next(r for r in resumen if r["llave"] == row["llave"] and r["procesos"] == "1")
                    self.assertAlmostEqual(float(row["speedup"]), float(base["media_s"]) / float(row["media_s"]))


if __name__ == "__main__":
    unittest.main()
