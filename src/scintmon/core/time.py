"""Conversões apenas sob hipótese temporal explícita do usuário."""
from datetime import datetime, timedelta, timezone


def convert_time(raw: str, basis: str, offset_hours: float = -3):
    stamp = datetime.fromisoformat(raw)
    if basis == "raw":
        return None, None
    local_zone = timezone(timedelta(hours=offset_hours))
    if basis == "utc":
        utc = stamp.replace(tzinfo=timezone.utc)
        return utc.isoformat(), utc.astimezone(local_zone).isoformat()
    if basis == "local":
        local = stamp.replace(tzinfo=local_zone)
        return local.astimezone(timezone.utc).isoformat(), local.isoformat()
    raise ValueError("Base temporal deve ser raw, utc ou local")
