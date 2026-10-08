# Análise de cintilação ionosférica GNSS / SCINTMON

Projeto para estudar a dependência azimutal da cintilação na estação São Luís, MA.

## Estado atual

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

A página inicial usa HTML e CSS nativos, sem dependências externas.
