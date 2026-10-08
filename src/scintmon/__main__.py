"""Entrada CLI: exporte observações e diagnósticos sem conversão científica."""
import argparse
import csv
from dataclasses import asdict, fields
from pathlib import Path
from scintmon.io.sum_parser import Diagnostic, Observation, parse_sum


def main():
    parser = argparse.ArgumentParser(description="Validar e exportar arquivos SCINTMON .SUM")
    parser.add_argument("files", nargs="+", type=Path)
    parser.add_argument("--output", type=Path, default=Path("outputs/tables"))
    args = parser.parse_args()
    # Valida todos os cabeçalhos antes de escrever produtos parciais.
    results = [parse_sum(path) for path in args.files]
    args.output.mkdir(parents=True, exist_ok=True)
    for filename, model, rows in (
        ("observations.csv", Observation, [o for r in results for o in r.observations]),
        ("parser_diagnostics.csv", Diagnostic, [d for r in results for d in r.diagnostics]),
    ):
        with (args.output / filename).open("w", newline="", encoding="utf-8") as stream:
            writer = csv.DictWriter(stream, fieldnames=[f.name for f in fields(model)])
            writer.writeheader()
            writer.writerows(asdict(row) for row in rows)
    print(f"{len(results)} arquivo(s); {sum(len(r.observations) for r in results)} observações; "
          f"{sum(len(r.diagnostics) for r in results)} diagnósticos. Horário bruto; unidades não confirmadas.")


if __name__ == "__main__":
    main()
