"""Diagnóstico de todos os arquivos fornecidos, inclusive cabeçalhos rejeitados."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from scintmon.io.sum_parser import parse_sum

failed = False
for filename in sys.argv[1:]:
    try:
        result = parse_sum(filename)
        print(f"{Path(filename).name}: {len(result.observations)} observações; {len(result.diagnostics)} diagnósticos")
        for issue in result.diagnostics:
            print(f"  linha {issue.linha}: {issue.tipo_problema}: {issue.acao_tomada}")
    except (ValueError, OSError, UnicodeError) as error:
        failed = True
        print(f"ERRO: {error}", file=sys.stderr)
if len(sys.argv) < 2:
    print("Uso: python scripts/validate_dataset.py ARQUIVO.sum [OUTROS.sum]", file=sys.stderr)
    failed = True
sys.exit(1 if failed else 0)
