"""Processamento completo reprodutível pelo terminal, usando o mesmo pipeline da UI."""
import argparse
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
import pandas as pd
from scintmon.analysis.pipeline import Options, build_dataset, filter_data
from scintmon.analysis.context import attach_context
from scintmon.core.rules import profile
from scintmon.reporting.report_builder import export_bundle, report
from scintmon.visualization.charts import make_charts


def main():
    parser = argparse.ArgumentParser(description="Processar SUM, gerar gráficos, tabelas e relatório")
    parser.add_argument("files", nargs="+", type=Path)
    parser.add_argument("--output", type=Path, default=Path("outputs"))
    parser.add_argument("--geometry", action="store_true")
    parser.add_argument("--station-unit", choices=["auto", "m", "km"], default="auto")
    parser.add_argument("--satellite-unit", choices=["auto", "m", "km"], default="auto")
    parser.add_argument("--time-basis", choices=["raw", "utc", "local"], default="raw")
    parser.add_argument("--offset", type=float, default=-3)
    parser.add_argument("--profile", choices=["project_default", "kintner_fig8", "custom"], default="project_default")
    parser.add_argument("--lower", type=float, default=.3)
    parser.add_argument("--upper", type=float, default=.6)
    parser.add_argument("--minimum-elevation", type=float, default=30)
    parser.add_argument("--deduplicate-exact", action="store_true")
    parser.add_argument("--individual-prns", action="store_true")
    parser.add_argument("--geomagnetic-csv", type=Path)
    parser.add_argument("--solar-csv", type=Path)
    args = parser.parse_args()
    options = Options(input_time_basis=args.time_basis, local_utc_offset_hours=args.offset,
                      station_unit=args.station_unit, satellite_unit=args.satellite_unit,
                      geometry_enabled=args.geometry, deduplicate_exact=args.deduplicate_exact,
                      selected_profile=profile(args.profile, lower=args.lower, upper=args.upper,
                                               minimum_elevation=args.minimum_elevation))
    dataset = build_dataset(args.files, options)
    dataset.data = attach_context(dataset.data, geomagnetic=pd.read_csv(args.geomagnetic_csv) if args.geomagnetic_csv else None,
                                  solar=pd.read_csv(args.solar_csv) if args.solar_csv else None)
    selected = filter_data(dataset.data, mask=args.geometry)
    note = f"Perfil {args.profile}; máscara ativa={args.geometry}; tempo={args.time_basis}; duplicatas excluídas={args.deduplicate_exact}"
    if not dataset.stations.empty and dataset.stations["station"].eq("DEMONSTRAÇÃO SINTÉTICA").any():
        note += "; DEMONSTRAÇÃO SINTÉTICA: dados artificiais, sem resultados observacionais"
    figures = make_charts(selected, note=note)
    bundle = export_bundle(dataset, selected, note, figures, individual_prns=args.individual_prns)
    args.output.mkdir(parents=True, exist_ok=True)
    (args.output / "scintmon_outputs.zip").write_bytes(bundle)
    md, html = report(dataset, selected, note, figures)
    reports = args.output / "reports"
    reports.mkdir(exist_ok=True)
    (reports / "report.md").write_text(md, encoding="utf-8")
    (reports / "report.html").write_text(html, encoding="utf-8")
    print(f"{len(dataset.data)} observações preservadas; {len(selected)} no recorte; {len(dataset.diagnostics)} diagnósticos. Produtos: {args.output}")


if __name__ == "__main__":
    main()
