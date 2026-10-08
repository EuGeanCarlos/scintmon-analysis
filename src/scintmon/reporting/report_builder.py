"""Relatório sem linguagem causal, exportável e reproduzível."""
from dataclasses import asdict
from html import escape
from io import BytesIO
import json
from zipfile import ZipFile, ZIP_DEFLATED
import pandas as pd
from scintmon.analysis.statistics import hourly, summarize
from scintmon.core.rules import REGISTRY
from scintmon.visualization.static import export_figure
from scintmon.visualization.charts import series, skyplot


def interpretation(data):
    if data.empty:
        return "Não há observações válidas no recorte selecionado; nenhum resultado foi calculado."
    sentences = []
    def geometry_text(value):
        return "não calculado" if pd.isna(value) else f"{float(value):.2f}°"
    for _, row in summarize(data, ["night"]).iterrows():
        sentences.append(f"Na noite {row['night']}, o recorte contém {row['n_valid']} observações válidas. "
            f"O maior S4 foi {row['max']:.3f}, no PRN {row.get('peak_prn')}, em {row.get('peak_time_raw')} "
            f"(horário bruto), elevação {geometry_text(row.get('peak_elevation'))}, azimute {geometry_text(row.get('peak_azimuth'))} "
            f"e quadrante {row.get('peak_quadrant') if pd.notna(row.get('peak_quadrant')) else 'não calculado'}. "
            f"A fração empírica S4 ≥ 0,60 foi {row['fraction_ge_06']:.1%}.")
    quadrants = summarize(data[data["quadrant"].notna()], ["quadrant"])
    if not quadrants.empty:
        row = quadrants.loc[quadrants["fraction_ge_06"].idxmax()]
        sentences.append(f"O quadrante {row['quadrant']} apresentou a maior fração empírica S4 ≥ 0,60 "
                         f"neste recorte: {row['fraction_ge_06']:.1%} de {row['n_valid']} observações válidas. "
                         "Empates são resolvidos pela ordem dos quadrantes; não se infere causalidade.")
    return "\n\n".join(sentences)


def report(dataset, selected, note, figures=None):
    sections = [
        ("Introdução", "Análise da dependência azimutal da cintilação ionosférica GNSS / SCINTMON – São Luís, MA."),
        ("Dados analisados", f"{len(dataset.stations)} arquivo(s); {len(dataset.data)} observações preservadas; {len(selected)} no recorte.\n{note}"),
        ("Metodologia", "Pipeline compartilhado: parser, validação, tempo declarado, geometria WGS84, filtros e estatística descritiva. Perfil ativo: " + dataset.options.selected_profile["label"]),
        ("Leitura do .SUM", "Layout do texto de requisitos; manual e arquivos das quatro noites ainda não validados. Duplicatas preservadas no conjunto completo. Campos auxiliares sem interpretação física confirmada."),
        ("S4", "S4² = (⟨I²⟩ − ⟨I⟩²) / ⟨I⟩²; de Paula, p. 5. S4 do .SUM não é recalculado da potência. Não finitos/negativos inválidos; acima de 1 preservados."),
        ("Transformação XYZ → ENU", "ΔXYZ é rotacionado pela matriz ESA Navipedia eq. 6. WGS84: a=6378137 m; 1/f=298.257223563 (NGA). Inferência de unidade é heurística registrada."),
        ("Azimute e elevação", "Az=atan2(E,N) mod 360; El=atan2(U,hypot(E,N)). Zênite/nadir não possuem azimute ou quadrante definido."),
        ("Máscara", "Projeto: elevação ≥30°. Kintner Fig. 8: elevação >10° e S4 >0,5; não é classificação forte. Personalizado: hipótese do usuário."),
        ("PRNs", "Resumo por noite e PRN inclui N, média, mediana, desvio padrão amostral, extremos, P90/P95 e frações empíricas. Produtos antes/depois da máscara no ZIP."),
        ("Quadrantes", "NE [0,90), SE [90,180), SO [180,270), NO [270,360). Azimute indefinido não é atribuído a um quadrante."),
        ("Comparação entre noites", "A noite é a data do cabeçalho; observações após meia-noite pertencem ao mesmo arquivo/noite. Não unir automaticamente arquivos com nome idêntico."),
        ("Resultados", interpretation(selected)),
        ("Discussão", "Diferenças entre quadrantes descrevem apenas a amostra e sua cobertura. Não demonstram causa nem probabilidade física universal."),
        ("Limitações", "Ausência dos .SUM reais, manual e plano original. Perfis do plano pendentes. Horário bruto por padrão; offset local fixo não incorpora horário de verão. Sem contexto fornecido, Kp/F10.7 permanecem ausentes. MATLAB não foi portado; divergência de largura de banda registrada."),
        ("Referências", "de Paula et al., PDF p. 5; Kintner e Ledvina, Fig. 8 p. 12; Burrell et al. (TEC); Malins et al. (2018); Cornell Simulator User Guide (2009). Matriz: docs/SOURCE_MATRIX.md. ESA: https://gssc.esa.int/navipedia/index.php/Transformations_between_ECEF_and_ENU_coordinates ; NGA: https://earth-info.nga.mil/index.php?action=wgs84&dir=wgs84")]
    markdown = "# Relatório de análise GNSS\n\n" + "\n\n".join(f"## {i}. {title}\n\n{text}" for i, (title, text) in enumerate(sections, 1))
    body = "".join(f"<section><h2>{i}. {escape(title)}</h2><p>{escape(text).replace(chr(10), '<br>')}</p></section>" for i, (title, text) in enumerate(sections, 1))
    for title, figure in (figures or {}).items():
        body += f"<section><h2>{escape(title)}</h2>" + figure.to_html(full_html=False, include_plotlyjs="inline" if title == next(iter(figures)) else False) + "</section>"
    html = '<!doctype html><html lang="pt-BR"><meta charset="utf-8"><title>Relatório GNSS</title><style>body{font:16px/1.6 system-ui;max-width:1100px;margin:3rem auto;padding:1rem;color:#17364a}h2{color:#086baf}section{margin:2rem 0}</style><h1>Relatório de análise GNSS</h1>' + body + "</html>"
    return markdown, html


def export_bundle(dataset, selected, note, figures, *, individual_prns=False, time_column="datetime_raw"):
    buffer = BytesIO()
    md, html = report(dataset, selected, note, figures)
    complete = dataset.data
    with ZipFile(buffer, "w", ZIP_DEFLATED) as archive:
        archive.writestr("reports/report.md", md)
        archive.writestr("reports/report.html", html)
        archive.writestr("metadata.json", json.dumps(dict(options=asdict(dataset.options), filters=note,
                           scientific_rules=REGISTRY), ensure_ascii=False, indent=2))
        tables = {"complete": complete, "filtered": selected, "parser_diagnostics": dataset.diagnostics,
                  "stations": dataset.stations}
        if not complete.empty:
            retained = complete[~complete["excluded_exact_duplicate"]]
            tables.update(prn_before=summarize(retained, ["night", "prn"]),
                          prn_after=summarize(retained[retained["passes_active_selection"]], ["night", "prn"]),
                          quadrants=summarize(selected[selected["quadrant"].notna()], ["night", "quadrant"]),
                          nights=summarize(selected, ["night"]),
                          hourly_raw=hourly(selected, "datetime_raw"),
                          geomagnetic=summarize(selected, ["night", "geomagnetic_condition"]),
                          solar_period_from_plan=summarize(selected, ["night", "solar_cycle_period_from_plan"]))
            if selected["datetime_utc"].notna().any():
                tables["hourly_utc"] = hourly(selected, "datetime_utc")
                tables["hourly_local"] = hourly(selected, "datetime_local")
        for name, table in tables.items():
            archive.writestr(f"tables/{name}.csv", table.to_csv(index=False))
        parquet = BytesIO()
        complete.to_parquet(parquet, index=False)
        archive.writestr("tables/complete.parquet", parquet.getvalue())
        for name, figure in figures.items():
            archive.writestr(f"figures/{name}.html", figure.to_html(include_plotlyjs="inline"))
            for format in ["png", "svg"]:
                archive.writestr(f"figures/{name}.{format}", export_figure(figure, format))
        if individual_prns and not selected.empty:
            for (night, prn), sample in selected.groupby(["night", "prn"]):
                individual = {field: series(sample, field, time_column,
                    note=note + f" · noite {night} · PRN {prn}")
                    for field in ["s4", "signal_power_raw", "elevation_deg", "azimuth_deg"]}
                individual["elevation_deg"].add_hline(y=30, line_dash="dash")
                individual["skyplot"] = skyplot(sample, note)
                for name, figure in individual.items():
                    base = f"figures/prn/{night}/PRN_{prn}_{name}"
                    archive.writestr(base + ".html", figure.to_html(include_plotlyjs="inline"))
                    for format in ["png", "svg"]:
                        archive.writestr(f"{base}.{format}", export_figure(figure, format))
    return buffer.getvalue()
