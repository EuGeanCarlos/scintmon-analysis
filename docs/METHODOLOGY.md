# Pipeline e reprodutibilidade

1. A fonte .SUM lê cabeçalho e blocos. Erro fatal de cabeçalho é explícito; registros inconsistentes geram diagnósticos.
2. Cada observação mantém arquivo, linha, bloco, campos originais e S4 fornecido.
3. Tempo só é convertido mediante base declarada. Geometria WGS84 é opt-in; interface solicita/mostra unidades inferidas.
4. O conjunto completo não sofre filtros científicos. Recortes podem selecionar noite, PRN, quadrante, hora, condição calma e perfil.
5. Estatísticas descritivas e figuras usam somente S4 válido no recorte. O controle de qualidade sempre consulta o conjunto completo.
6. Relatório determinístico não atribui causalidade a quadrantes ou correlações.
7. ZIP inclui parâmetros, regras, dados originais aceitos, diagnósticos, tabelas antes/depois da seleção, Parquet, relatório e figuras.

## Contexto externo

Geomagnético: CSV com `datetime_utc,kp,dst,source`. Sem `interval_end_utc`, associa-se apenas no instante exato. Se o fim for fornecido, usa-se intervalo [início,fim), sem sobreposição e sem inventar validade de três horas. Fonte obrigatória e timestamps únicos. Nenhum contexto é associado sem UTC disponível.

Solar: CSV com `date,f107,sunspot_number,solar_cycle_class,source`. Uma linha por data UTC. Datas não presentes permanecem vazias. As fontes devem documentar unidades e método de obtenção.

## Arquitetura

`io/`: fontes, parser e demonstração; `core/`: geodésia, tempo e regras; `analysis/`: pipeline, contexto e estatísticas; `visualization/`: Plotly e renderização estática; `reporting/`: texto e pacote; `ui/`: controles e exibição. `app.py` apenas inicia o dashboard. Scripts usam os mesmos módulos. `RinexSource` é contrato futuro e falha explicitamente, sem tratar .SUM como RINEX.

## Limitações

Testes analíticos e demonstração não validam os dados instrumentais reais. A matriz inicial de fontes ainda exige revisão científica integral. Não implementamos estimação física de probabilidade, previsão, TEC a partir de .SUM ou o simulador MATLAB, que não fazem parte da análise observacional solicitada. Não há mudança de banco; os produtos são arquivos locais.
