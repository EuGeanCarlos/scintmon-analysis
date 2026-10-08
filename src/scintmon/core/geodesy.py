"""Rotação ECEF -> ENU segundo ESA Navipedia, equação 6.

Latitude e longitude geodéticas devem ser fornecidas explicitamente.
Não inferimos datum, coordenadas ou unidades dos arquivos .SUM.
"""
from dataclasses import dataclass
from math import atan2, cos, degrees, hypot, isfinite, radians, sin


@dataclass(frozen=True)
class Geometry:
    east_m: float
    north_m: float
    up_m: float
    range_m: float
    azimuth_deg: float | None
    elevation_deg: float
    quadrant: str | None


def quadrant(azimuth_deg: float) -> str:
    """Quadrantes geográficos com limites inferiores inclusivos.

    Convenção do projeto: NE [0,90), SE [90,180), SO [180,270),
    NO [270,360). 360° é normalizado para 0°; negativos não são aceitos.
    """
    if not isfinite(azimuth_deg) or not 0 <= azimuth_deg <= 360:
        raise ValueError("Azimute deve estar entre 0 e 360 graus")
    return ("NE", "SE", "SO", "NO")[int((azimuth_deg % 360) // 90)]


def satellite_geometry(station_xyz, satellite_xyz, *, station_unit: str,
                       satellite_unit: str, latitude_deg: float,
                       longitude_deg: float) -> Geometry:
    """Converta a linha de visada em geometria local, com saída em metros.

    Unidades da estação e satélite são independentes e obrigatórias.
    A latitude fornecida deve ser geodética, pois a vertical ENU é a
    normal ao elipsoide, não necessariamente o raio geocêntrico.
    """
    if not isfinite(latitude_deg) or not -90 <= latitude_deg <= 90:
        raise ValueError("Latitude inválida")
    if not isfinite(longitude_deg) or not -180 <= longitude_deg <= 180:
        raise ValueError("Longitude inválida")
    scales = {"m": 1, "km": 1000}
    if station_unit not in scales or satellite_unit not in scales:
        raise ValueError("Unidades devem ser m ou km")
    if len(station_xyz) != 3 or len(satellite_xyz) != 3:
        raise ValueError("XYZ exige três componentes")
    if not all(isfinite(v) for v in (*station_xyz, *satellite_xyz)):
        raise ValueError("XYZ deve conter valores finitos")
    dx, dy, dz = [sat * scales[satellite_unit] - sta * scales[station_unit]
                  for sta, sat in zip(station_xyz, satellite_xyz)]
    lat, lon = radians(latitude_deg), radians(longitude_deg)
    # Subtrair a estação antes de rotacionar é necessário para obter
    # a direção do satélite vista pelo receptor, não pelo centro da Terra.
    east = -sin(lon) * dx + cos(lon) * dy
    north = -sin(lat) * cos(lon) * dx - sin(lat) * sin(lon) * dy + cos(lat) * dz
    up = cos(lat) * cos(lon) * dx + cos(lat) * sin(lon) * dy + sin(lat) * dz
    horizontal = hypot(east, north)
    distance = hypot(horizontal, up)
    if distance == 0:
        raise ValueError("Estação e satélite coincidentes: direção indefinida")
    # No zênite/nadir o azimute é indefinido. A tolerância relativa
    # só absorve arredondamento numérico, não é máscara científica.
    azimuth = None if horizontal <= distance * 1e-12 else degrees(atan2(east, north)) % 360
    return Geometry(east, north, up, distance, azimuth,
                    degrees(atan2(up, horizontal)),
                    None if azimuth is None else quadrant(azimuth))


def passes_elevation(elevation_deg: float, minimum_deg: float) -> bool:
    """Máscara inclusiva, sem remover a observação original."""
    if not isfinite(minimum_deg) or not -90 <= minimum_deg <= 90:
        raise ValueError("Máscara deve estar entre -90 e 90 graus")
    return isfinite(elevation_deg) and -90 <= elevation_deg <= 90 and elevation_deg >= minimum_deg
