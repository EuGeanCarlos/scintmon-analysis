"""Tabela canônica auditável; nenhuma linha é descartada por filtros científicos."""
from dataclasses import asdict, dataclass, field
from datetime import datetime
import logging
import pandas as pd
from scintmon.core.geodesy import ecef_to_geodetic, infer_unit, satellite_geometry
from scintmon.core.rules import APP_CONFIG, classify_s4, profile, rule_value
from scintmon.core.time import convert_time
from scintmon.io.sources import ScintmonSumSource

logger = logging.getLogger(__name__)


@dataclass
class Options:
    input_time_basis: str = "raw"
    local_utc_offset_hours: float = -3
    station_unit: str = "auto"
    satellite_unit: str = "auto"
    geometry_enabled: bool = False
    latitude: float | None = None
    longitude: float | None = None
    selected_profile: dict = field(default_factory=profile)
    deduplicate_exact: bool = False


@dataclass
class Dataset:
    data: pd.DataFrame
    diagnostics: pd.DataFrame
    stations: pd.DataFrame
    options: Options


def build_dataset(paths, options=None):
    options = options or Options()
    # Valida base temporal mesmo em uma coleção vazia.
    convert_time("2000-01-01T00:00:00", options.input_time_basis, options.local_utc_offset_hours)
    rows, diagnostics, stations = [], [], []
    source = ScintmonSumSource()
    for path in paths:
        result = source.read(path)
        diagnostics.extend(asdict(d) for d in result.diagnostics)
        station_info = dict(source_file=result.source_file, station=result.station,
                            header_datetime_raw=result.header_datetime_raw,
                            header_aux_raw=result.header_aux_raw,
                            receiver_x=result.station_xyz_raw[0], receiver_y=result.station_xyz_raw[1],
                            receiver_z=result.station_xyz_raw[2])
        station_unit = options.station_unit
        lat, lon = options.latitude, options.longitude
        station_error = None
        if options.geometry_enabled:
            try:
                station_unit = infer_unit(result.station_xyz_raw) if station_unit == "auto" else station_unit
                derived_lat, derived_lon, height = ecef_to_geodetic(result.station_xyz_raw, station_unit)
                if (lat is None) != (lon is None):
                    raise ValueError("Latitude e longitude devem ser fornecidas juntas")
                lat = derived_lat if lat is None else lat
                lon = derived_lon if lon is None else lon
                station_info.update(latitude_deg=lat, longitude_deg=lon, height_m=height,
                                    derived_latitude_deg=derived_lat, derived_longitude_deg=derived_lon,
                                    station_unit=station_unit,
                                    coordinate_unit_inferred=options.station_unit == "auto")
                bounds = APP_CONFIG["expected_station_bounds"]
                if not bounds["latitude"][0] <= derived_lat <= bounds["latitude"][1] or not bounds["longitude"][0] <= derived_lon <= bounds["longitude"][1]:
                    diagnostics.append(dict(arquivo=result.source_file, linha=3,
                        tipo_problema="estacao_fora_regiao_esperada", conteudo_original=str(result.station_xyz_raw),
                        acao_tomada="Posição preservada; verificar estação/datum. Limites são heurística regional."))
            except ValueError as error:
                station_error = str(error)
                diagnostics.append(dict(arquivo=result.source_file, linha=3, tipo_problema="geometria_estacao",
                                        conteudo_original=str(result.station_xyz_raw), acao_tomada=station_error))
        stations.append(station_info)
        night = result.header_datetime_raw[:10]
        for observation in result.observations:
            row = asdict(observation)
            utc, local = convert_time(row["datetime_raw"], options.input_time_basis, options.local_utc_offset_hours)
            row.update(station=result.station, night=night, observation_date=row["datetime_raw"][:10],
                       datetime_utc=utc, datetime_local=local,
                       input_time_basis=options.input_time_basis,
                       local_utc_offset_hours=options.local_utc_offset_hours,
                       s4_class_project=classify_s4(row["s4"], profile()),
                       s4_class_active=classify_s4(row["s4"], options.selected_profile),
                       s4_gt_03=row["s4_valid"] and row["s4"] > .3,
                       s4_ge_03=row["s4_valid"] and row["s4"] >= .3,
                       s4_gt_05=row["s4_valid"] and row["s4"] > .5,
                       s4_ge_06=row["s4_valid"] and row["s4"] >= .6,
                       azimuth_deg=None, elevation_deg=None, quadrant=None,
                       passes_mask_10=False, passes_mask_30=False, passes_active_mask=False,
                       geometry_valid=False, coordinate_unit_inferred=False,
                       excluded_exact_duplicate=options.deduplicate_exact and row["exact_duplicate"],
                       kp=None, dst=None, f107=None, sunspot_number=None,
                       geomagnetic_condition="não fornecida", solar_cycle_class=None,
                       solar_cycle_period_from_plan=None,
                       receiver_x=result.station_xyz_raw[0], receiver_y=result.station_xyz_raw[1],
                       receiver_z=result.station_xyz_raw[2])
            for label, (start, end) in rule_value("solar_periods").items():
                if start <= int(night[:4]) <= end:
                    row["solar_cycle_period_from_plan"] = label
            if options.geometry_enabled and station_error is None:
                try:
                    sat_xyz = (row["x_sat_raw"], row["y_sat_raw"], row["z_sat_raw"])
                    sat_unit = infer_unit(sat_xyz, "satellite") if options.satellite_unit == "auto" else options.satellite_unit
                    geometry = satellite_geometry(result.station_xyz_raw, sat_xyz,
                        station_unit=station_unit, satellite_unit=sat_unit, latitude_deg=lat, longitude_deg=lon)
                    row.update(asdict(geometry), geometry_valid=True, station_unit=station_unit,
                               satellite_unit=sat_unit, station_latitude_deg=lat, station_longitude_deg=lon,
                               coordinate_unit_inferred="auto" in (options.station_unit, options.satellite_unit))
                    el = geometry.elevation_deg
                    p = options.selected_profile
                    row.update(passes_mask_10=el >= rule_value("operational_elevation"),
                               passes_mask_30=el >= rule_value("project_elevation"),
                               passes_active_mask=el > p["minimum_elevation"] if p["strict_elevation"] else el >= p["minimum_elevation"])
                except ValueError as error:
                    diagnostics.append(dict(arquivo=result.source_file, linha=row["line_number"],
                        tipo_problema="geometria_observacao", conteudo_original=row["original_line"], acao_tomada=str(error)))
            row["passes_active_selection"] = (row["s4_valid"] and row["passes_active_mask"] and
                (row["s4"] > options.selected_profile.get("s4_gt", -1)))
            if row["elevation_deg"] is not None and row["elevation_deg"] < 0:
                diagnostics.append(dict(arquivo=result.source_file, linha=row["line_number"],
                    tipo_problema="elevacao_negativa", conteudo_original=row["original_line"],
                    acao_tomada="Preservada; observação abaixo do horizonte"))
            rows.append(row)
    logger.info("Arquivos=%d observações=%d diagnósticos=%d", len(stations), len(rows), len(diagnostics))
    return Dataset(pd.DataFrame(rows), pd.DataFrame(diagnostics,
        columns=["arquivo", "linha", "tipo_problema", "conteudo_original", "acao_tomada"]),
        pd.DataFrame(stations), options)


def filter_data(data, *, nights=None, prns=None, quadrants=None, mask=False,
                time_column="datetime_raw", hour_range=None, valid_only=True, calm_only=False):
    """Filtros retornam cópia; intervalos horários incluem ambas as horas."""
    if data.empty:
        return data.copy()
    selected = data.copy()
    selected = selected[~selected["excluded_exact_duplicate"]]
    if valid_only:
        selected = selected[selected["s4_valid"]]
    if nights is not None:
        selected = selected[selected["night"].isin(nights)]
    if prns is not None:
        selected = selected[selected["prn"].isin(prns)]
    if quadrants is not None:
        selected = selected[selected["quadrant"].isin(quadrants)]
    if mask:
        selected = selected[selected["passes_active_selection"]]
    if calm_only:
        selected = selected[selected["geomagnetic_condition"] == "calma pelo critério do plano"]
    if hour_range is not None:
        hours = selected[time_column].map(lambda v: datetime.fromisoformat(v).hour if isinstance(v, str) else None)
        start, end = hour_range
        selected = selected[hours.between(start, end) if start <= end else ((hours >= start) | (hours <= end))]
    return selected.copy()
