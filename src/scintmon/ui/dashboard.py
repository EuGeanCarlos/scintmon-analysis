"""Dashboard: controles, feedback e visualização; sem duplicar cálculo científico."""
from dataclasses import asdict
from io import BytesIO
from pathlib import Path
import hashlib
import json
import tempfile
import pandas as pd
import streamlit as st
from scintmon.analysis.context import attach_context
from scintmon.analysis.pipeline import Options, build_dataset, filter_data
from scintmon.analysis.statistics import summarize
from scintmon.core.rules import REGISTRY, ROOT, profile
from scintmon.io.demo import demo_files
from scintmon.reporting.report_builder import export_bundle, interpretation, report
from scintmon.visualization.charts import make_charts, series, skyplot
from scintmon.visualization.static import export_figure

SECTIONS = ["Visão Geral", "PRNs", "Geometria", "Quadrantes", "Comparação de Noites",
            "Controle de Qualidade", "Metodologia e Fontes", "Exportações"]


@st.cache_data(show_spinner=False)
def load_dataset(files, options):
    with tempfile.TemporaryDirectory() as directory:
        paths = []
        for name, content in files:
            path = Path(directory) / Path(name).name
            path.write_bytes(content)
            paths.append(path)
        return build_dataset(paths, options)


def csv_button(label, data, name):
    st.download_button(label, data.to_csv(index=False).encode("utf-8-sig"),
                       file_name=name, mime="text/csv", key=name)


def show_chart(figure, key):
    st.plotly_chart(figure, width="stretch", key=key,
                   config={"displaylogo": False, "toImageButtonOptions": {"format": "png"}})
    if st.checkbox("Preparar PNG e SVG deste gráfico", key="images_" + key):
        left, right = st.columns(2)
        left.download_button("Baixar PNG", export_figure(figure, "png"), key="png_" + key,
                             file_name=key + ".png", mime="image/png")
        right.download_button("Baixar SVG", export_figure(figure, "svg"), key="svg_" + key,
                              file_name=key + ".svg", mime="image/svg+xml")


def main():
    st.set_page_config(page_title="SCINTMON · Análise GNSS", page_icon="🛰️", layout="wide")
    st.markdown("""<style>
    h1{letter-spacing:-.035em}h2{letter-spacing:-.02em}
    [data-testid=stMetric]{background:white;border:1px solid #e1eaf0;border-radius:16px;padding:18px}
    [data-testid=stSidebar]{background:rgba(255,255,255,.94)}
    button:active{transform:scale(.99)}
    @media(prefers-reduced-motion:reduce){button:active{transform:none}}
    @media(prefers-contrast:more){[data-testid=stMetric]{border-color:#17364a}}
    </style>""", unsafe_allow_html=True)
    st.caption("SCINTMON / GNSS · ESTAÇÃO SÃO LUÍS, MARANHÃO")
    st.title("Cintilação ionosférica")
    st.write("Do sinal observado à análise por direção, com hipóteses e fontes visíveis.")
    with st.sidebar:
        st.header("Dados e critérios")
        mode = st.radio("Fonte de dados", ["Arquivos reais", "Demonstração sintética"], key="source_mode")
        uploads = st.file_uploader("Importar arquivos .SUM", type=["sum"], accept_multiple_files=True)
        local_files = sorted((ROOT / "data/raw").glob("*.sum")) + sorted((ROOT / "data/raw").glob("*.SUM"))
        use_local = st.checkbox("Ler também data/raw", value=False)
        with st.form("criteria"):
            profile_name = st.selectbox("Perfil científico", list(REGISTRY["profiles"]),
                                        format_func=lambda name: REGISTRY["profiles"][name]["label"])
            lower = st.number_input("Limite fraca → moderada (perfil custom)", min_value=0.0, value=.3, step=.05)
            upper = st.number_input("Limite moderada → forte (perfil custom)", min_value=0.0, value=.6, step=.05)
            custom_el = st.number_input("Elevação mínima (perfil custom, °)", min_value=0.0, max_value=90.0, value=30.0)
            basis = st.selectbox("Base temporal do arquivo (hipótese explícita)", ["raw", "utc", "local"],
                                 format_func=lambda v: {"raw":"Não confirmada · manter bruto", "utc":"Arquivo em UTC", "local":"Arquivo em horário local"}[v])
            offset = st.number_input("Offset local fixo em horas", min_value=-23.0, max_value=23.0, value=-3.0)
            geometry = st.checkbox("Calcular geometria WGS84", value=True)
            station_unit = st.selectbox("Unidade XYZ da estação", ["auto", "m", "km"])
            satellite_unit = st.selectbox("Unidade XYZ dos satélites", ["auto", "m", "km"])
            dedup = st.checkbox("Excluir duplicatas exatas apenas dos recortes", value=False)
            st.form_submit_button("Aplicar critérios", width="stretch")
        try:
            active = profile(profile_name, lower=lower, upper=upper, minimum_elevation=custom_el)
        except ValueError as error:
            st.error(str(error))
            st.stop()
        with st.expander("Contexto solar e geomagnético"):
            kp_upload = st.file_uploader("CSV geomagnético", type="csv", key="kp")
            solar_upload = st.file_uploader("CSV solar", type="csv", key="solar")
            st.caption("Nenhum índice é preenchido sem dados e fonte. Veja o guia para o contrato temporal.")
    selected_section = st.radio("Área de análise", SECTIONS, horizontal=True, label_visibility="collapsed", key="section")
    st.caption(f"Perfil ativo: {active['label']} · Base temporal: {basis} · Offset local: {offset:+g} h")
    if profile_name == "custom":
        st.warning("Critério personalizado pelo usuário; não corresponde necessariamente a uma classificação publicada.")
    if basis == "raw":
        st.info("Base temporal não confirmada: UTC, hora local e associação de contexto ficam indisponíveis.")
    if station_unit == "auto" or satellite_unit == "auto":
        st.caption("Unidades automáticas são inferências por magnitude e ficam registradas na tabela; confira o manual.")
    if mode == "Demonstração sintética":
        files = demo_files()
        st.warning("DEMONSTRAÇÃO SINTÉTICA · Todos os valores desta amostra foram gerados para testar a aplicação. Não são resultados de São Luís.")
    else:
        files = [(upload.name, upload.getvalue()) for upload in uploads or []]
        if use_local:
            files += [(path.name, path.read_bytes()) for path in local_files]
    if len({name for name, _ in files}) != len(files):
        st.error("Há arquivos com nomes repetidos. Renomeie-os para preservar a identidade de cada fonte.")
        st.stop()
    if selected_section == "Metodologia e Fontes":
        st.subheader("Objetivo e regras científicas")
        st.write("Caracterizar a dependência azimutal do S4 por PRN, noite, horário e quadrante, com controle de qualidade e contexto quando fornecido.")
        for rule in REGISTRY["rules"]:
            with st.expander(rule["purpose"] + " · " + rule["status"]):
                st.json(rule)
        st.markdown((ROOT / "docs/SOURCE_MATRIX.md").read_text(encoding="utf-8"))
        return
    if not files:
        st.info("Importe seus arquivos .SUM para iniciar, ou escolha a demonstração sintética na lateral.")
        st.write("A aplicação preserva as observações originais e registra os filtros utilizados em cada exportação.")
        return
    options = Options(input_time_basis=basis, local_utc_offset_hours=offset,
                      station_unit=station_unit, satellite_unit=satellite_unit,
                      geometry_enabled=geometry, selected_profile=active, deduplicate_exact=dedup)
    try:
        with st.spinner("Lendo dados e calculando a tabela canônica…"):
            dataset = load_dataset(files, options)
        dataset.data = attach_context(dataset.data,
            geomagnetic=pd.read_csv(BytesIO(kp_upload.getvalue())) if kp_upload else None,
            solar=pd.read_csv(BytesIO(solar_upload.getvalue())) if solar_upload else None)
    except (ValueError, UnicodeError, OSError) as error:
        st.error(f"Não foi possível processar os dados: {error}")
        st.stop()
    if dataset.data.empty:
        st.warning("Nenhuma observação aceita. Confira os diagnósticos.")
        st.dataframe(dataset.diagnostics, width="stretch")
        return
    data = dataset.data
    with st.sidebar:
        st.divider()
        st.subheader("Recorte de análise")
        nights = st.multiselect("Noites", sorted(data["night"].unique()), default=sorted(data["night"].unique()))
        prns = st.multiselect("PRNs", sorted(data["prn"].unique()), default=sorted(data["prn"].unique()))
        use_quadrants = st.checkbox("Filtrar quadrantes", value=False)
        quadrants = st.multiselect("Quadrantes", ["NE", "SE", "SO", "NO"], default=["NE", "SE", "SO", "NO"])
        apply_mask = st.checkbox("Aplicar seleção do perfil", value=geometry)
        columns = ["datetime_raw"] + (["datetime_utc", "datetime_local"] if basis != "raw" else [])
        time_column = st.selectbox("Base do eixo temporal", columns,
                                   format_func=lambda v: {"datetime_raw":"Bruto", "datetime_utc":"UTC", "datetime_local":"Local"}[v])
        use_hours = st.checkbox("Filtrar faixa horária", value=False)
        start_hour = st.number_input("Hora inicial (inclusiva)", 0, 23, 0)
        end_hour = st.number_input("Hora final (inclusiva)", 0, 23, 5)
        calm = st.checkbox("Somente Kp ≤ 3", disabled=not kp_upload or basis == "raw")
        occurrence_threshold = st.number_input("Limiar de ocorrência S4", min_value=0.0, value=.6, step=.05)
        occurrence_strict = st.checkbox("Ocorrência com comparação estrita >", value=False)
        thresholds = st.multiselect("Linhas de referência S4", [.3, .5, .6], default=[.3, .6])
        heatmap_metric = st.selectbox("Estatística do heatmap", ["mean", "max"])
    filtered = filter_data(data, nights=nights, prns=prns, quadrants=quadrants if use_quadrants else None,
                           mask=apply_mask, time_column=time_column,
                           hour_range=(start_hour, end_hour) if use_hours else None, calm_only=calm)
    time_label = {"datetime_raw":"bruto", "datetime_utc":"UTC", "datetime_local":"local"}[time_column]
    note = (f"Perfil: {active['label']}; noites: {', '.join(nights) or 'nenhuma'}; "
            f"PRNs: {', '.join(str(p) for p in prns) or 'nenhum'}; "
            f"quadrantes: {', '.join(quadrants) if use_quadrants else 'todos'}; "
            f"seleção: {'ativa' if apply_mask else 'sem máscara'}; tempo: {time_label}; "
            f"horas: {str(start_hour) + '–' + str(end_hour) if use_hours else 'todas'}; "
            f"Kp ≤3: {'sim' if calm else 'sem filtro'}; duplicatas: {'excluídas no recorte' if dedup else 'preservadas'}" +
            ("; DEMONSTRAÇÃO SINTÉTICA" if mode == "Demonstração sintética" else ""))
    with st.expander("Ver filtros aplicados"):
        st.caption(note)
    if not kp_upload:
        st.caption("Dados geomagnéticos não fornecidos.")
    if not solar_upload:
        st.caption("Dados de atividade solar não fornecidos.")
    if selected_section == "Controle de Qualidade":
        st.subheader("Auditoria dos dados completos")
        st.dataframe(dataset.diagnostics, width="stretch")
        counts = {"S4 > 1": int(data["s4_above_one"].sum()), "S4 inválido": int((~data["s4_valid"]).sum()),
                  "Duplicatas exatas preservadas": int(data["exact_duplicate"].sum()),
                  "Geometria inválida/ausente": int((~data["geometry_valid"]).sum()),
                  "Elevação negativa": int(data["elevation_deg"].lt(0).sum())}
        st.json(counts)
        st.dataframe(data, width="stretch")
        csv_button("Baixar diagnósticos", dataset.diagnostics, "parser_diagnostics.csv")
        return
    if selected_section == "Geometria":
        st.subheader("XYZ → ΔXYZ → ENU → Azimute / Elevação")
        st.dataframe(dataset.stations, width="stretch")
        if not geometry:
            st.info("Ative o cálculo WGS84 para mostrar a geometria.")
            return
    if filtered.empty:
        st.warning("Não há observações válidas para o recorte. Confira os filtros e diagnósticos.")
        if selected_section != "Exportações":
            return
    if selected_section == "PRNs" and not filtered.empty:
        night = st.selectbox("Noite do satélite", sorted(filtered["night"].unique()))
        available = filtered[filtered["night"] == night]
        prn = st.selectbox("Satélite PRN", sorted(available["prn"].unique()))
        sample = available[available["prn"] == prn]
        before = data[(data["night"] == night) & (data["prn"] == prn) & ~data["excluded_exact_duplicate"]]
        st.dataframe(pd.concat([summarize(before, ["night", "prn"]).assign(recorte="Antes dos filtros"),
                               summarize(sample, ["night", "prn"]).assign(recorte="Recorte ativo")]), width="stretch")
        st.caption("Painéis mostram apenas o PRN e a noite selecionados; linhas de referência são critérios do projeto.")
        for field in ["s4", "signal_power_raw", "elevation_deg", "azimuth_deg"]:
            figure = series(sample, field, time_column, note=note + f" · PRN {prn} · noite {night}", thresholds=thresholds if field == "s4" else ())
            if field == "elevation_deg":
                figure.add_hline(y=30, line_dash="dash")
            show_chart(figure, "prn_" + field)
        show_chart(skyplot(sample, note), "prn_skyplot")
        return
    figures = make_charts(filtered, time_column=time_column, note=note, thresholds=thresholds,
                          occurrence_threshold=occurrence_threshold, occurrence_strict=occurrence_strict,
                          heatmap_metric=heatmap_metric)
    if selected_section == "Visão Geral":
        cols = st.columns(3) + st.columns(3)
        metrics = ["Noites", "Observações completas", "No recorte", "PRNs no recorte", "S4 máximo", "S4 médio"]
        values = [data["night"].nunique(), len(data), len(filtered), filtered["prn"].nunique(),
                  f"{filtered['s4'].max():.3f}", f"{filtered['s4'].mean():.3f}"]
        for col, name, value in zip(cols, metrics, values):
            col.metric(name, value)
        st.write(interpretation(filtered))
        for key in ["serie_s4", "heatmap", "todos_prns"]:
            show_chart(figures[key], key)
    elif selected_section == "Geometria":
        for key in ["skyplot", "elevation_deg", "azimuth_deg", "s4_vs_elevation_deg", "s4_vs_signal_power_raw"]:
            show_chart(figures[key], key)
    elif selected_section == "Quadrantes":
        st.dataframe(summarize(filtered, ["night", "quadrant"]), width="stretch")
        for key in ["quadrantes_box", "ocorrencia", "media_horaria"]:
            show_chart(figures[key], key)
    elif selected_section == "Comparação de Noites":
        for key in ["noites", "noites_ocorrencia"]:
            show_chart(figures[key], key)
        for groups in [["night"], ["night", "prn"], ["night", "quadrant"]]:
            st.dataframe(summarize(filtered, groups), width="stretch")
        if kp_upload:
            st.subheader("Comparação por condição geomagnética fornecida")
            st.dataframe(summarize(filtered, ["night", "geomagnetic_condition"]), width="stretch")
        if solar_upload:
            st.subheader("Comparação por classe solar fornecida")
            st.dataframe(summarize(filtered, ["night", "solar_cycle_class"]), width="stretch")
    elif selected_section == "Exportações":
        st.subheader("Produtos científicos e auditoria")
        csv_button("Dados filtrados CSV", filtered, "filtered.csv")
        csv_button("Dados completos CSV", data, "complete.csv")
        parquet = BytesIO()
        data.to_parquet(parquet, index=False)
        st.download_button("Dados completos Parquet", parquet.getvalue(), file_name="complete.parquet")
        csv_button("Resumo PRNs", summarize(filtered, ["night", "prn"]), "prn_summary.csv")
        csv_button("Resumo quadrantes", summarize(filtered, ["night", "quadrant"]), "quadrant_summary.csv")
        md, html = report(dataset, filtered, note, figures)
        st.download_button("Relatório HTML interativo", html.encode("utf-8"), "report.html", "text/html")
        st.download_button("Relatório Markdown", md.encode("utf-8"), "report.md", "text/markdown")
        st.caption("O pacote inclui dados completos e filtrados, antes/depois da seleção, regras, parâmetros e todos os gráficos em HTML, PNG e SVG.")
        individual_prns = st.checkbox("Incluir também quatro painéis e sky plot para cada PRN/noite no ZIP", value=False)
        fingerprint = hashlib.sha256(repr((files, asdict(options), note, occurrence_threshold, occurrence_strict, heatmap_metric, thresholds,
                                          kp_upload.getvalue() if kp_upload else None, solar_upload.getvalue() if solar_upload else None,
                                          individual_prns)).encode()).hexdigest()
        if st.button("Gerar pacote completo ZIP"):
            with st.spinner("Renderizando figuras e montando relatório…"):
                st.session_state["export"] = (fingerprint, export_bundle(dataset, filtered, note, figures,
                                              individual_prns=individual_prns, time_column=time_column))
        cached = st.session_state.get("export")
        if cached and cached[0] == fingerprint:
            st.download_button("Baixar pacote científico", cached[1], file_name="scintmon_outputs.zip", mime="application/zip")
