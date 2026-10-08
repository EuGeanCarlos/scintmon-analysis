"""Validação da integração parser -> CLI -> produtos CSV."""
import csv
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


class CliTests(unittest.TestCase):
    def test_geometry_export_requires_explicit_parameters(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            source = root / "synthetic.sum"
            source.write_text("Estação sintética\nTeste\n6378000 0 0\n2002 12 01 21 01\naux\n"
                              "2101 1 82\n1 6378.1 0.1 0 0 100 0 0.2 0 0\n", encoding="utf-8")
            output = root / "products"
            base = [sys.executable, "-m", "scintmon", str(source), "--output", str(output)]
            incomplete = subprocess.run(base + ["--station-unit", "m"], capture_output=True)
            self.assertNotEqual(incomplete.returncode, 0)
            self.assertFalse(output.exists())
            complete = subprocess.run(base + ["--station-unit", "m", "--satellite-unit", "km",
                                             "--latitude", "0", "--longitude", "0",
                                             "--minimum-elevation", "30"], capture_output=True)
            self.assertEqual(complete.returncode, 0, complete.stderr)
            with (output / "geometry.csv").open(encoding="utf-8", newline="") as stream:
                row = next(csv.DictReader(stream))
            self.assertAlmostEqual(float(row["elevation_deg"]), 45)
            self.assertEqual(row["quadrant"], "SE")
            self.assertEqual(row["passes_elevation"], "True")

    def test_export_observations_and_diagnostics(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            source = root / "021201H0.sum"
            source.write_text("Sao Luis, Brasil\nDescrição\n1 2 3\n2002 12 01 21 01\naux\n"
                              "2101 1 82\n1 1 2 3 0 1164 0 1.2 0 0\n", encoding="utf-8")
            output = root / "output"
            command = subprocess.run([sys.executable, "-m", "scintmon", str(source),
                                      "--output", str(output)], capture_output=True, text=True)
            self.assertEqual(command.returncode, 0, command.stderr)
            with (output / "observations.csv").open(encoding="utf-8", newline="") as stream:
                rows = list(csv.DictReader(stream))
            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0]["s4"], "1.2")
            self.assertEqual(rows[0]["s4_above_one"], "True")
            with (output / "parser_diagnostics.csv").open(encoding="utf-8", newline="") as stream:
                diagnostics = list(csv.DictReader(stream))
            self.assertEqual(diagnostics[0]["tipo_problema"], "s4_acima_de_um")
