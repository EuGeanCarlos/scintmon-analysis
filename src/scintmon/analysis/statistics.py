"""Estatísticas descritivas: denominador explícito de S4 válido, sem causalidade."""
import pandas as pd


def summarize(data, groups):
    records = []
    if data.empty:
        return pd.DataFrame()
    grouped = data.groupby(groups, dropna=False, sort=True)
    for key, sample in grouped:
        key = key if isinstance(key, tuple) else (key,)
        valid = sample[sample["s4_valid"]]
        values = valid["s4"]
        has_strength_classes = valid["s4_class_active"].isin(["fraca", "moderada", "forte"]).any()
        record = dict(zip(groups, key))
        record.update(n_total=len(sample), n_valid=len(valid), n_mask_30=int(sample["passes_mask_30"].sum()),
                      n_active=int(sample["passes_active_selection"].sum()),
                      mean=values.mean(), median=values.median(), std=values.std(ddof=1),
                      min=values.min(), max=values.max(), p90=values.quantile(.90), p95=values.quantile(.95),
                      fraction_ge_03=(values >= .3).mean() if len(valid) else None,
                      fraction_gt_05=(values > .5).mean() if len(valid) else None,
                      fraction_ge_06=(values >= .6).mean() if len(valid) else None,
                      percent_weak=100 * (valid["s4_class_active"] == "fraca").mean() if has_strength_classes else None,
                      percent_moderate=100 * (valid["s4_class_active"] == "moderada").mean() if has_strength_classes else None,
                      percent_strong=100 * (valid["s4_class_active"] == "forte").mean() if has_strength_classes else None,
                      power_mean=valid["signal_power_raw"].mean(), power_median=valid["signal_power_raw"].median())
        if len(valid):
            # Empates: primeira observação na ordem original; nada é deduplicado.
            peak = valid.loc[values.idxmax()]
            record.update(peak_time_raw=peak["datetime_raw"], peak_prn=peak["prn"],
                          peak_elevation=peak["elevation_deg"], peak_azimuth=peak["azimuth_deg"],
                          peak_quadrant=peak["quadrant"], peak_power=peak["signal_power_raw"])
        records.append(record)
    return pd.DataFrame(records)


def hourly(data, time_column="datetime_raw"):
    selected = data[data["s4_valid"]].copy()
    if selected.empty:
        return pd.DataFrame()
    # Parsing individual mantém a hora da base escolhida; não reconverte LT para UTC.
    selected["hour"] = selected[time_column].map(lambda v: int(v[11:13]) if isinstance(v, str) else None)
    return selected.groupby(["night", "quadrant", "hour"], dropna=False)["s4"].agg(["mean", "max", "count"]).reset_index()
