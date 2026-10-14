# Análise de cintilação GNSS / SCINTMON

Ferramentas Python e dashboard Streamlit para análise de cintilação ionosférica. O Pages publica somente a página de apresentação em site/; o dashboard precisa de servidor Python.

## Tecnologias

- Python
- Streamlit
- HTML
- CSS

## Funcionalidades e utilização

Para o dashboard, consulte docs/RUNNING.md; para a página estática, abra site/index.html.

## Como executar

```bash
git clone https://github.com/EuGeanCarlos/scintmon-analysis.git
cd scintmon-analysis
```

Para o dashboard, consulte docs/RUNNING.md; para a página estática, abra site/index.html.

## Demonstração e publicação

Execução local. Nenhuma demonstração nova foi confirmada nesta etapa.

GitHub Pages hospeda arquivos estáticos e não executa Java, Node.js, PHP ou Python. As dependências de servidor deste projeto devem ser executadas em ambiente apropriado.

## Estrutura versionada

```text
.github/workflows/pages.yml
.github/workflows/tests.yml
.gitignore
.streamlit/config.toml
README.md
app.py
config/app_config.yaml
config/scientific_rules.yaml
docs/DATA_DICTIONARY.md
docs/DELIVERY.md
docs/DEPENDENCIES.md
docs/GEOMETRY.md
docs/METHODOLOGY.md
docs/RUNNING.md
docs/SCIENTIFIC_RULES.md
docs/SOURCE_MATRIX.md
docs/USER_GUIDE.md
pyproject.toml
references/manifest.json
requirements-lock.txt
requirements.txt
scripts/process_all.py
…
```

## Status

Protótipo / projeto de estudo em desenvolvimento. A descrição acima distingue o que está implementado das dependências ou etapas pendentes.

## Autor e créditos

**Gean Carlos** — estudante de Engenharia de Computação, UEMA.

[GitHub](https://github.com/EuGeanCarlos)

Licenças, autoria compartilhada e atribuições existentes no código e nos materiais originais permanecem aplicáveis.

---

## Documentação original e contexto

O material original a seguir preserva contexto, créditos e planejamento. Para execução e limitações atuais, considere as seções de auditoria acima.

# Análise de cintilação ionosférica GNSS / SCINTMON

Projeto para estudar a dependência azimutal da cintilação na estação São Luís, MA.

## Estado atual

Dashboard interativo implementado em Python/Streamlit: importação de .SUM, tabela canônica, geodésia WGS84, três perfis S4, filtros, séries por PRN, sky plots, quadrantes, comparação de noites, contexto CSV opcional, controle de qualidade, fontes e exportação CSV/Parquet/PNG/SVG/HTML/ZIP. [Como executar](docs/RUNNING.md).

Implementação testada com amostra sintética, sem validação instrumental com as quatro noites reais. Manual SCINTMON e plano original continuam pendentes. O simulador MATLAB e a fonte RINEX futura não são implementações observacionais desta etapa.

Geometria local ECEF → ENU, azimute, elevação, quadrantes e máscara inclusiva disponíveis por CLI com unidades e localização explícitas. Consulte [a metodologia e os parâmetros](docs/GEOMETRY.md). Latitude/longitude ainda não são derivadas automaticamente de XYZ.

Primeira etapa Python implementada: parser `.SUM`, diagnósticos de qualidade, preservação de duplicatas e exportação CSV por terminal. Consulte [o guia de execução](docs/USER_GUIDE.md). Testes automatizados usam casos sintéticos; validação com arquivos reais permanece pendente.

Página inicial estática em português, inspirada na referência visual fornecida, com superfícies claras e cores azul, ciano e verde. Sem resultados simulados. Onze fontes foram catalogadas em [docs/SOURCE_MATRIX.md](docs/SOURCE_MATRIX.md), com hashes em [references/manifest.json](references/manifest.json). Ainda faltam os arquivos .SUM, o manual SCINTMON e o plano original. A revisão integral das fontes precederá a implementação científica.

## Publicação

O workflow publica `site/` no GitHub Pages a cada atualização de `main`. GitHub Pages hospeda a interface estática; a futura aplicação Python/Streamlit exigirá hospedagem com execução Python.

## Próximas etapas

1. Inspecionar os dados e referências.
2. Documentar fontes e regras científicas confirmadas.
3. Implementar parser, geodésia e estatísticas com testes.
4. Integrar gráficos, exportações e relatórios.

## Visualização local

Abra `site/index.html` no navegador.

## Dependências

A página estática usa HTML e CSS nativos. A aplicação Python usa as dependências de `requirements.txt`; [justificativas](docs/DEPENDENCIES.md). [Regras científicas](docs/SCIENTIFIC_RULES.md), [dicionário](docs/DATA_DICTIONARY.md) e [metodologia](docs/METHODOLOGY.md).
