"""Associação de contexto somente com tempo UTC declarado e fontes informadas."""
import pandas as pd
from scintmon.core.rules import rule_value


def attach_context(data, *, geomagnetic=None, solar=None):
    result = data.copy()
    if result.empty:
        return result
    if geomagnetic is not None:
        required = {"datetime_utc", "kp", "dst", "source"}
        if not required.issubset(geomagnetic.columns):
            raise ValueError("Contexto geomagnético exige datetime_utc, kp, dst e source")
        context = geomagnetic.copy()
        if context["source"].fillna("").str.strip().eq("").any():
            raise ValueError("Contexto deve informar source em todas as linhas")
        context["timestamp"] = pd.to_datetime(context["datetime_utc"], utc=True, errors="raise")
        if context["timestamp"].duplicated().any():
            raise ValueError("Contexto geomagnético tem timestamps duplicados")
        for field in ["kp", "dst"]:
            context[field] = pd.to_numeric(context[field], errors="raise")
        if (~context["kp"].between(0, 9) & context["kp"].notna()).any():
            raise ValueError("Kp deve estar no intervalo 0 a 9")
        # Sem duração fornecida, associação somente no instante exato.
        # Isso evita inventar a validade temporal de um índice do arquivo.
        ends = None
        if "interval_end_utc" in context:
            ends = pd.to_datetime(context["interval_end_utc"], utc=True, errors="raise")
            if (ends <= context["timestamp"]).any():
                raise ValueError("Fim de intervalo deve suceder o início")
            ordered = context.assign(end=ends).sort_values("timestamp")
            if (ordered["timestamp"].iloc[1:].to_numpy() < ordered["end"].iloc[:-1].to_numpy()).any():
                raise ValueError("Intervalos geomagnéticos sobrepostos")
        times = pd.to_datetime(result["datetime_utc"], utc=True)
        for index, row in context.iterrows():
            match = times.eq(row["timestamp"]) if ends is None else (times.ge(row["timestamp"]) & times.lt(ends.loc[index]))
            result.loc[match, ["kp", "dst"]] = [row["kp"], row["dst"]]
            result.loc[match, "geomagnetic_source"] = row["source"]
        result["geomagnetic_condition"] = result["kp"].map(lambda kp: "não fornecida" if pd.isna(kp) else
            "calma pelo critério do plano" if kp <= rule_value("quiet_kp") else "acima do critério calmo")
    if solar is not None:
        if not {"date", "f107", "sunspot_number", "solar_cycle_class", "source"}.issubset(solar.columns):
            raise ValueError("Contexto solar exige date, f107, sunspot_number, solar_cycle_class e source")
        context = solar.copy()
        context["date"] = pd.to_datetime(context["date"], errors="raise").dt.strftime("%Y-%m-%d")
        if context["date"].duplicated().any() or context["source"].fillna("").str.strip().eq("").any():
            raise ValueError("Datas solares duplicadas ou fonte ausente")
        for field in ["f107", "sunspot_number"]:
            context[field] = pd.to_numeric(context[field], errors="raise")
            if context[field].dropna().lt(0).any():
                raise ValueError("Índices solares não podem ser negativos")
        for _, row in context.iterrows():
            # A data é UTC quando disponível. Sem UTC, nenhum contexto é atribuído.
            match = result["datetime_utc"].map(lambda v: v[:10] if isinstance(v, str) else None).eq(row["date"])
            for field in ["f107", "sunspot_number", "solar_cycle_class"]:
                result.loc[match, field] = row[field]
            result.loc[match, "solar_source"] = row["source"]
    return result
