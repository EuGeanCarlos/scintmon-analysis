"""Entrada CLI: exporte observações e diagnósticos sem conversão científica."""
import argparse
import csv
from dataclasses import asdict, fields
from pathlib import Path
from scintmon.io.sum_parser import Diagnostic, Observation, parse_sum
from scintmon.core.geodesy import Geometry, passes_elevation, satellite_geometry


def main():
    parser = argparse.ArgumentParser(description="Validar e exportar arquivos SCINTMON .SUM")
    parser.add_argument("files", nargs="+", type=Path)
    parser.add_argument("--output", type=Path, default=Path("outputs/tables"))
    parser.add_argument("--station-unit", choices=["m", "km"])
    parser.add_argument("--satellite-unit", choices=["m", "km"])
    parser.add_argument("--latitude", type=float)
    parser.add_argument("--longitude", type=float)
    parser.add_argument("--minimum-elevation", type=float)
    args = parser.parse_args()
    geometry_options = (args.station_unit, args.satellite_unit, args.latitude,
                        args.longitude, args.minimum_elevation)
    geometry_enabled = any(value is not None for value in geometry_options)
    if geometry_enabled and any(value is None for value in geometry_options):
        parser.error("Geometria exige unidades, latitude, longitude e máscara explícitas")
    # Valida todos os cabeçalhos antes de escrever produtos parciais.
    results = [parse_sum(path) for path in args.files]
    geometry_rows = []
    if geometry_enabled:
        # Valida a máscara mesmo quando os arquivos não contêm observações.
        passes_elevation(0, args.minimum_elevation)
        for result in results:
            for observation in result.observations:
                geometry = satellite_geometry(
                    result.station_xyz_raw,
                    (observation.x_sat_raw, observation.y_sat_raw, observation.z_sat_raw),
                    station_unit=args.station_unit, satellite_unit=args.satellite_unit,
                    latitude_deg=args.latitude, longitude_deg=args.longitude)
                geometry_rows.append(dict(
                    source_file=result.source_file, line_number=observation.line_number,
                    **asdict(geometry),
                    passes_elevation=passes_elevation(geometry.elevation_deg, args.minimum_elevation),
                    station_unit=args.station_unit, satellite_unit=args.satellite_unit,
                    latitude_deg=args.latitude, longitude_deg=args.longitude,
                    minimum_elevation_deg=args.minimum_elevation))
    args.output.mkdir(parents=True, exist_ok=True)
    for filename, model, rows in (
        ("observations.csv", Observation, [o for r in results for o in r.observations]),
        ("parser_diagnostics.csv", Diagnostic, [d for r in results for d in r.diagnostics]),
    ):
        with (args.output / filename).open("w", newline="", encoding="utf-8") as stream:
            writer = csv.DictWriter(stream, fieldnames=[f.name for f in fields(model)])
            writer.writeheader()
            writer.writerows(asdict(row) for row in rows)
    if geometry_enabled:
        names = ["source_file", "line_number"] + [f.name for f in fields(Geometry)] + [
            "passes_elevation", "station_unit", "satellite_unit", "latitude_deg",
            "longitude_deg", "minimum_elevation_deg"]
        with (args.output / "geometry.csv").open("w", newline="", encoding="utf-8") as stream:
            writer = csv.DictWriter(stream, fieldnames=names)
            writer.writeheader()
            writer.writerows(geometry_rows)
    print(f"{len(results)} arquivo(s); {sum(len(r.observations) for r in results)} observações; "
          f"{sum(len(r.diagnostics) for r in results)} diagnósticos. Horário bruto; unidades não confirmadas.")


if __name__ == "__main__":
    main()
