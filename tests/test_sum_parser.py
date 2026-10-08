"""Casos sintéticos: não representam medições reais das quatro noites."""
import tempfile
import unittest
from pathlib import Path
from scintmon.io.sum_parser import parse_sum

HEADER = "Sao Luis, Brasil\nDescrição\n1 2 3\n2002 12 01 21 01\nauxiliar\n"
SAT = "1 10320.3 -10810.3 -21787.6 0 1164 0 0.25 0 0\n"


class ParserTests(unittest.TestCase):
    def parse(self, body, header=HEADER):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "021201H0(1).sum"
            path.write_text(header + body, encoding="utf-8")
            return parse_sum(path)

    def test_known_values(self):
        result = self.parse("2101 2 82\n" + SAT + "2 1 2 3 0 2823 0 0.23 0 0\n")
        first, second = result.observations
        self.assertEqual(result.station, "Sao Luis, Brasil")
        self.assertEqual((first.prn, first.x_sat_raw, first.y_sat_raw, first.z_sat_raw),
                         (1, 10320.3, -10810.3, -21787.6))
        self.assertEqual((first.signal_power_raw, first.s4), (1164, .25))
        self.assertEqual((second.signal_power_raw, second.s4), (2823, .23))
        self.assertEqual(result.diagnostics, [])

    def test_duplicate_preservation_and_block_auxiliary(self):
        result = self.parse("2101 2 82\n" + SAT * 2 + "2101 1 83\n" + SAT)
        self.assertEqual(len(result.observations), 3)
        self.assertEqual([o.exact_duplicate for o in result.observations], [False, True, False])

    def test_midnight_and_unexpected_reversal(self):
        result = self.parse("2359 1 82\n" + SAT + "0001 1 82\n" + SAT + "0000 1 82\n" + SAT)
        self.assertEqual(result.observations[1].datetime_raw, "2002-12-02T00:01:00")
        self.assertIn("horario_inconsistente", [d.tipo_problema for d in result.diagnostics])

    def test_s4_invalid_and_above_one_preserved(self):
        rows = [SAT.replace("0.25", value) for value in ("-1", "nan", "inf", "1.2")]
        result = self.parse("2101 4 82\n" + "".join(rows))
        self.assertEqual([o.s4_valid for o in result.observations], [False, False, False, True])
        self.assertTrue(result.observations[-1].s4_above_one)
        self.assertEqual(result.observations[-1].s4, 1.2)

    def test_corruption_and_count_diagnostics(self):
        result = self.parse("2101 3 82\n" + SAT + "bad row\n")
        self.assertEqual(len(result.observations), 1)
        self.assertEqual({d.tipo_problema for d in result.diagnostics}, {"numero_campos", "contagem_bloco"})

    def test_invalid_block_does_not_reuse_previous_time(self):
        result = self.parse("2101 1 82\n" + SAT + "2560 1 82\n" + SAT)
        self.assertEqual(len(result.observations), 1)
        self.assertIn("registro_sem_bloco", [d.tipo_problema for d in result.diagnostics])

    def test_invalid_header_fails_explicitly(self):
        with self.assertRaisesRegex(ValueError, "cabeçalho inválido"):
            self.parse("", "incompleto\n")


if __name__ == "__main__":
    unittest.main()
