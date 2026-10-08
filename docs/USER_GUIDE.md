# Primeira etapa executável

Requisitos: Python 3.11 ou superior. Parser e CLI usam somente a biblioteca padrão; não há dependência científica nova nesta etapa.

No PowerShell, a partir da raiz do projeto:

```powershell
$env:PYTHONPATH = 'src'
python -m unittest discover -s tests -v
python -m scintmon data/raw/021201H0.sum --output outputs/tables
```

Passe vários caminhos para analisar mais de um arquivo. Arquivos com sufixo `(1)` são aceitos; coloque o caminho entre aspas no terminal.

## Produtos

- `observations.csv`: observações, horário bruto, campos auxiliares, linha original e flags de qualidade.
- `parser_diagnostics.csv`: arquivo, linha, problema, conteúdo e ação.

Os CSVs de uma execução substituem os produtos anteriores no diretório indicado. Use diretórios diferentes para conservar execuções distintas. Cabeçalhos inválidos interrompem a execução com erro explícito antes de gerar os CSVs.

## Limites científicos

Layout baseado no texto do projeto, ainda sem validação contra o manual e os arquivos reais. XYZ permanece em unidade não confirmada. Não há conversão UTC/local, cálculo de geometria, filtro de elevação nem classificação científica nesta etapa. S4 do arquivo é preservado; negativos e não finitos são marcados inválidos e valores acima de 1 não são truncados. Duplicatas permanecem na saída. As contagens de bloco incluem linhas candidatas rejeitadas; consulte também os diagnósticos de registros.

Os testes usam dados sintéticos e valores descritos no texto fornecido; não substituem regressão com as quatro noites reais. `raw_5`, `raw_7`, `raw_9`, `raw_10`, auxiliares e potência permanecem sem significado físico inferido.
