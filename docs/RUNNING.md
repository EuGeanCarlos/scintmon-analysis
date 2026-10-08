# Executar a aplicação

## Windows / PowerShell

Na raiz do repositório:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m streamlit run app.py --server.address 127.0.0.1 --server.port 8501
```

Abra http://127.0.0.1:8501. Não é necessário ativar o ambiente. Python >=3.11.

## Linux / macOS

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m streamlit run app.py
```

## Fluxo de uso

1. Importe .SUM (vários arquivos; ambos os nomes com/sem `(1)` funcionam). Ou coloque em `data/raw/` e marque a leitura local.
2. Confira perfil, hipótese temporal, unidade da estação e satélites. Selecione `raw` quando UTC/local não estiverem documentados.
3. Aplique os critérios e veja o Controle de Qualidade; não interprete observações com geometria ausente como se passassem a máscara.
4. Escolha noites, PRNs, quadrantes, faixa horária e base do eixo temporal. Intervalo horário que cruza meia-noite é suportado. Para 0h–6h exclusivo do limite final, selecione horas 0–5 (horas incluídas integralmente).
5. Explore as oito áreas. PRNs contém quatro séries e sky plot individuais. Na Geometria, a trajetória abaixo do horizonte é omitida somente do sky plot.
6. Em Exportações, baixe CSV, Parquet, resumos ou relatório. Gere o ZIP para figuras PNG/SVG/HTML, parâmetros e auditoria. PNG/SVG de cada gráfico também ficam disponíveis sob sua opção de preparação.

A demonstração possui quatro arquivos artificiais identificados `DEMO_*.sum`. Ela serve para explorar o produto e executar testes. Nenhum valor é resultado observacional da estação real.

## Processamento em lote

```powershell
.\.venv\Scripts\python.exe scripts/process_all.py data/raw/021201H0.sum data/raw/021202H0.sum --geometry --station-unit auto --satellite-unit auto --time-basis raw --output outputs
.\.venv\Scripts\python.exe scripts/validate_dataset.py data/raw/021201H0.sum
```

O primeiro comando gera ZIP e `outputs/reports/report.md` / `report.html`. Para gerar quatro painéis e sky plot de cada PRN/noite, acrescente `--individual-prns`. Para base UTC confirmada, use `--time-basis utc --offset -3`. `--profile kintner_fig8` aplica seleção estrita. Perfil `custom` aceita `--lower`, `--upper`, `--minimum-elevation`. Contexto opcional via `--geomagnetic-csv` e `--solar-csv`; contratos em `METHODOLOGY.md`.

O comando básico documentado em `USER_GUIDE.md` continua disponível sem dependências científicas: `python -m scintmon ...` com `PYTHONPATH=src`. Produtos com nome igual no mesmo diretório são substituídos; use diretórios distintos para preservar execuções.

## Testes

```powershell
$env:PYTHONPATH = 'src'
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

CI executa testes em Python 3.11, 3.12 e 3.13. Cobertura funcional: parser, erros e duplicatas, tempo, regras e limites, geodésia contra PyProj, filtros, estatísticas, contexto, exportação/relatório e navegação do Streamlit.

## Hospedagem

GitHub Pages hospeda `site/`, a página estática de apresentação. Não executa Python. A aplicação interativa é executada localmente; implantação pública requer serviço Python (por exemplo Streamlit Community Cloud) e não foi configurada nesta etapa. Dados importados ficam no processo local e não são enviados ao GitHub. PDFs/código MATLAB originais não são publicados.
