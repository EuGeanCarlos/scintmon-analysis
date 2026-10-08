"""Gráficos derivados da tabela canônica, com bases e filtros identificados."""
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from scintmon.analysis.statistics import hourly, summarize

COLORS = ["#0874bc", "#08a1c2", "#07b6b8", "#21bd91", "#7865ac", "#de833c"]
px.defaults.color_discrete_sequence = COLORS
LABELS = {"s4": "S4 (adimensional)", "signal_power_raw": "Potência bruta (unidade não confirmada)",
          "elevation_deg": "Elevação (°)", "azimuth_deg": "Azimute (°)",
          "quadrant": "Quadrante", "night": "Noite (data do cabeçalho)",
          "datetime_raw": "Horário bruto", "datetime_utc": "Horário UTC", "datetime_local": "Horário local"}


def finish(fig, title, note):
    import textwrap
    fig.update_layout(template="plotly_white", title=title, colorway=COLORS,
                      font=dict(family="Arial, sans-serif", color="#17364a"),
                      margin=dict(l=60, r=35, t=75, b=max(100, 15 * len(textwrap.wrap(note, 85)) + 30)), height=520,
                      legend_title_text="PRN / quadrante")
    fig.add_annotation(text="<br>".join(textwrap.wrap(note, 85)), x=0, y=-.25, xref="paper", yref="paper", showarrow=False,
                       xanchor="left", align="left", font=dict(size=10))
    return fig


def series(data, field="s4", time_column="datetime_raw", title=None, note="", thresholds=()):
    fig = px.line(data.sort_values(["source_file", "prn", time_column]), x=time_column, y=field,
                  color=data.sort_values(["source_file", "prn", time_column])["prn"].astype(str),
                  line_group="source_file", markers=True, labels=LABELS,
                  hover_data=["source_file", "line_number", "quadrant"])
    for value in thresholds:
        fig.add_hline(y=value, line_dash="dot", annotation_text=f"Referência S4 {value}")
    if field == "s4" and not data.empty:
        peak = data.loc[data["s4"].idxmax()]
        fig.add_annotation(x=peak[time_column], y=peak["s4"], xref="x", yref="y",
                           text=f"Máximo: {peak['s4']:.3f}", showarrow=True)
    return finish(fig, title or f"{LABELS[field]} × tempo", note)


def skyplot(data, note=""):
    visible = data[data["elevation_deg"].notna() & data["azimuth_deg"].notna() & data["elevation_deg"].ge(0)].copy()
    visible["zenith_angle"] = 90 - visible["elevation_deg"]
    fig = px.scatter_polar(visible, r="zenith_angle", theta="azimuth_deg", color="s4",
                           hover_data=["prn", "elevation_deg", "source_file", "datetime_raw"],
                           color_continuous_scale="Teal", labels=LABELS)
    fig.update_layout(polar=dict(angularaxis=dict(direction="clockwise", rotation=90),
        radialaxis=dict(range=[0, 90], tickvals=[0, 30, 60, 80, 90],
                        ticktext=["90°", "60°", "30°", "10°", "0°"])))
    # As linhas de trajetória não unem satélites ou arquivos diferentes.
    for (source, prn), sample in visible.groupby(["source_file", "prn"]):
        sample = sample.sort_values("datetime_raw")
        fig.add_trace(go.Scatterpolar(r=sample["zenith_angle"], theta=sample["azimuth_deg"],
                         mode="lines", name=f"PRN {prn} · {source}", line=dict(width=1), opacity=.4))
    fig.add_trace(go.Scatterpolar(r=[60] * 361, theta=list(range(361)), mode="lines",
                                  name="Elevação 30°", line=dict(color="#086baf", dash="dash")))
    return finish(fig, "Trajetória no céu · cor = S4", note + " · Abaixo do horizonte e zênite sem azimute omitidos apenas neste gráfico")


def make_charts(data, *, time_column="datetime_raw", note="", thresholds=(.3, .5, .6),
                occurrence_threshold=.6, occurrence_strict=False, heatmap_metric="mean"):
    if data.empty:
        return {}
    figures = {"serie_s4": series(data, time_column=time_column, note=note, thresholds=thresholds)}
    for field in ["signal_power_raw", "elevation_deg", "azimuth_deg"]:
        figures[field] = series(data, field, time_column, note=note)
        if field == "elevation_deg":
            figures[field].add_hline(y=30, line_dash="dash", annotation_text="Máscara do projeto 30°")
    figures["skyplot"] = skyplot(data, note)
    with_quadrants = data[data["quadrant"].notna()]
    figures["quadrantes_box"] = finish(px.box(with_quadrants, x="quadrant", y="s4", color="quadrant",
        category_orders={"quadrant": ["NE", "SE", "SO", "NO"]}, labels=LABELS, points="outliers"), "Distribuição de S4 por quadrante", note)
    occurrence = with_quadrants.groupby("quadrant")["s4"].agg(
        fraction=lambda v: (v > occurrence_threshold).mean() if occurrence_strict else (v >= occurrence_threshold).mean(), n="count").reset_index()
    figures["ocorrencia"] = finish(px.bar(occurrence, x="quadrant", y="fraction", color="quadrant", text="n",
        labels={"fraction": "Fração empírica de observações", "quadrant": "Quadrante"}),
        f"Ocorrência relativa · S4 {'>' if occurrence_strict else '≥'} {occurrence_threshold:g} · rótulo = N", note)
    figures["ocorrencia"].update_yaxes(range=[0, 1])
    hour_data = hourly(data, time_column)
    figures["media_horaria"] = finish(px.line(hour_data, x="hour", y="mean", color="quadrant", line_group="night",
        markers=True, hover_data=["night", "count"], labels={"hour": f"Hora · {LABELS[time_column]}", "mean": "S4 médio"}),
        "S4 médio horário por quadrante", note)
    heat = data.copy()
    heat["hour"] = heat[time_column].map(lambda v: int(v[11:13]) if isinstance(v, str) else None)
    pivot = heat.pivot_table(index="prn", columns="hour", values="s4", aggfunc=heatmap_metric)
    figures["heatmap"] = finish(go.Figure(go.Heatmap(z=pivot.to_numpy(), x=pivot.columns, y=pivot.index,
        colorscale="Teal", colorbar=dict(title=f"S4 {heatmap_metric}"))), f"PRN × hora · S4 {heatmap_metric}", note)
    figures["heatmap"].update_xaxes(title=f"Hora · {LABELS[time_column]}", type="category")
    figures["heatmap"].update_yaxes(title="PRN", type="category")
    nights = summarize(data, ["night"])
    figures["noites"] = finish(px.bar(nights, x="night", y=["mean", "max", "p95"], barmode="group",
        labels={"value": "S4 (adimensional)", "night": "Noite"}), "Comparação entre noites · média, máximo e P95", note)
    figures["noites_ocorrencia"] = finish(px.bar(nights, x="night", y=["fraction_ge_03", "fraction_gt_05", "fraction_ge_06"],
        barmode="group", labels={"value": "Fração empírica", "night": "Noite"}), "Ocorrência relativa por noite", note)
    for field in ["elevation_deg", "signal_power_raw"]:
        figures[f"s4_vs_{field}"] = finish(px.scatter(data, x=field, y="s4", color=data["prn"].astype(str), labels=LABELS,
            hover_data=["source_file", "datetime_raw"]), f"S4 × {LABELS[field]}", note)
        if field == "elevation_deg":
            figures[f"s4_vs_{field}"].add_vrect(x0=-90, x1=30, fillcolor="#08a1c2", opacity=.1, line_width=0)
    prns = sorted(data["prn"].unique())
    fig = make_subplots(rows=len(prns), cols=1, subplot_titles=[f"PRN {p}" for p in prns])
    for i, prn in enumerate(prns, 1):
        for source, sample in data[data["prn"] == prn].groupby("source_file"):
            sample = sample.sort_values(time_column)
            fig.add_trace(go.Scatter(x=sample[time_column], y=sample["s4"], mode="lines+markers",
                                    name=f"PRN {prn} · {source}"), row=i, col=1)
        fig.update_yaxes(title_text="S4", row=i, col=1)
    figures["todos_prns"] = finish(fig, "S4 por PRN · painéis individuais", note)
    figures["todos_prns"].update_layout(height=max(440, 220 * len(prns)))
    return figures
