# Entrega técnica — aplicação observacional

Data: 08/10/2026. Implementação funcional, com validação por dados sintéticos; validação instrumental pendente.

## Arquivos e responsabilidades

```text
app.py
config/                    regras científicas e configuração padrão
src/scintmon/
  io/                      parser SUM, contrato de fonte, demonstração
  core/                    regras, tempo, geodésia
  analysis/                tabela canônica, filtros, estatísticas, contexto
  visualization/           gráficos Plotly e exportação Matplotlib
  reporting/               interpretação determinística, relatórios e ZIP
  ui/                      dashboard Streamlit
scripts/                   processamento em lote e validação
tests/                     núcleo, CLI, exportação e interface
docs/                      fontes, regras, metodologia, dicionário e execução
references/manifest.json   catálogo de 11 arquivos; originais locais
site/                      apresentação estática no GitHub Pages
```

Pastas `data/raw`, `data/context` e `outputs` são destinos de dados/produtos locais. Os arquivos de entrada e produtos não são publicados no GitHub. A adição de `ui/` é justificada pela separação entre interface e cálculos; `app.py` não contém lógica científica. Dependências justificadas em `DEPENDENCIES.md`; `requirements-lock.txt` registra o ambiente Windows/Python 3.12 verificado, enquanto `requirements.txt` define faixas suportadas.

## Funções entregues

- Importação múltipla .SUM e diagnósticos; campos auxiliares e duplicatas preservados.
- Tabela canônica com rastreabilidade, validade S4, conversão temporal explícita e contexto ausente sinalizado.
- WGS84 ECEF → geodésico; ΔXYZ → ENU → Az/El; unidades independentes da estação e satélites, inferência registrada e alertas regionais.
- Perfis projeto, seleção Kintner e personalizado; filtros por noite, PRN, quadrante, hora e Kp calmo quando fornecido.
- Estatística antes/depois de seleção; média, mediana, desvio amostral, extremos, P90/P95, potência, máximo e frações empíricas.
- Oito áreas da interface em português, campos com hipóteses e fontes visíveis.
- Séries S4/potência/elevação/azimute, quatro painéis individuais, small multiples, sky plot, boxplot, ocorrência, médias horárias, heatmap, comparação de noites e dispersões S4 × elevação/potência.
- Exportação CSV, Parquet, figuras PNG/SVG/HTML, relatório Markdown/HTML e ZIP auditável. Opção para exportar cada PRN/noite separadamente.
- Scripts de processamento e validação usam os mesmos módulos da UI. RINEX mantém contrato futuro explícito.

## Fórmulas e parâmetros

Registro detalhado em `SCIENTIFIC_RULES.md` e `config/scientific_rules.yaml`. S4 não é recalculado da potência. WGS84 tem a=6378137 m e 1/f=298.257223563 (NGA). Rotação ENU segue ESA eq. 6. Az=atan2(E,N) mod360; El=atan2(U,hypot(E,N)). Desvio amostral ddof=1 e percentis lineares são convenções computacionais documentadas.

Perfil inicial: projeto (S4 <0,30; 0,30 ≤ S4 <0,60; S4 ≥0,60; elevação ≥30°). Base temporal inicial `raw`, sem conversão UTC/LT. Inferência de unidade é exibida como hipótese. Estes critérios do plano não são atribuídos aos artigos sem evidência.

## Verificação

36 testes aprovados no ambiente local Python 3.12. Foram verificados núcleo, CLI básica, gráficos PNG/SVG/ZIP, Parquet, geodésia contra PyProj, contextos, relatório, oito áreas do Streamlit e perfil personalizado sem geometria. Interface também inspecionada no navegador local. A demonstração gera 480 observações artificiais em quatro arquivos; essa contagem não representa as quatro noites instrumentais. CI configurada para Python 3.11, 3.12 e 3.13; os resultados remotos devem ser consultados no GitHub Actions após envio.

## Pendências científicas e de implantação

- Diagnóstico das noites reais de 01–04/12/2002: não executado, arquivos não fornecidos.
- Manual SCINTMON e plano original: não fornecidos. Unidades, datum, campo 6 e base temporal ainda precisam de confirmação documental.
- Revisão integral dos artigos: pendente; a matriz registra identificação e trechos já verificados.
- Simulador MATLAB: apenas referência catalogada; divergência de largura de banda e nome de função permanecem para revisão. Fonte RINEX: implementação futura conforme especificação.
- Hospedagem pública da aplicação Python: não configurada; Pages continua sendo apresentação estática. Dashboard executável localmente.

Comandos completos estão em `RUNNING.md`. Nenhum resultado científico real ou diagnóstico das noites ausentes foi fabricado.
