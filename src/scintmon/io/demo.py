"""Amostra sintética determinística exclusivamente para demonstração e testes."""
from datetime import datetime, timedelta
from math import cos, sin, radians, sqrt
from scintmon.core.rules import rule_value


def demo_files():
    # Coordenada escolhida para a simulação, sem representar levantamento
    # da estação real. ECEF deriva do elipsoide configurado no registro.
    lat, lon = radians(-2.5), radians(-44.3)
    a, f = rule_value("wgs84_a"), 1 / rule_value("wgs84_inverse_flattening")
    e2 = f * (2 - f)
    n = a / sqrt(1 - e2 * sin(lat) ** 2)
    station = (n * cos(lat) * cos(lon), n * cos(lat) * sin(lon), n * (1 - e2) * sin(lat))
    files = []
    for night in range(1, 5):
        header = ("DEMONSTRAÇÃO SINTÉTICA\nNão representa observações reais\n" +
                  " ".join(f"{v:.6f}" for v in station) + f"\n2002 12 {night:02d} 23 55\nsynthetic\n")
        body = []
        for minute in range(30):
            stamp = datetime(2002, 12, night, 23, 55) + timedelta(minutes=minute)
            body.append(f"{stamp:%H%M} 4 {minute}")
            for prn in range(1, 5):
                az = radians((prn - 1) * 90 + 15 + minute)
                el = radians(15 + (minute * 3 + prn * 8) % 65)
                east, north, up = [2e7 * v for v in (cos(el) * sin(az), cos(el) * cos(az), sin(el))]
                delta = (-sin(lon) * east - cos(lon) * sin(lat) * north + cos(lon) * cos(lat) * up,
                         cos(lon) * east - sin(lon) * sin(lat) * north + sin(lon) * cos(lat) * up,
                         cos(lat) * north + sin(lat) * up)
                xyz = [(s + d) / 1000 for s, d in zip(station, delta)]
                s4 = .1 + .95 * abs(sin(minute / 9 + prn / 2 + night / 3))
                body.append(f"{prn} {' '.join(f'{v:.6f}' for v in xyz)} 0 {1000 + 17 * minute + prn} 0 {s4:.4f} 0 0")
        files.append((f"DEMO_{night}.sum", (header + "\n".join(body) + "\n").encode("utf-8")))
    return files
