# Dependências da aplicação

Streamlit serve a interface Python e gerencia upload e downloads; Pandas e NumPy suportam a tabela canônica e estatísticas; Plotly fornece gráficos interativos; PyArrow habilita exportação Parquet; Matplotlib renderiza PNG/SVG sem exigir navegador externo; PyProj valida numericamente a conversão WGS84 implementada no projeto.

Essas dependências correspondem ao escopo da especificação GNSS. Não modificam o projeto B2B. O núcleo de parsing, geodésia, tempo e regras utiliza a biblioteca padrão. `scientific_rules.yaml` usa sintaxe JSON, que é subconjunto de YAML 1.2, para poder ser lido sem uma dependência adicional de YAML.
