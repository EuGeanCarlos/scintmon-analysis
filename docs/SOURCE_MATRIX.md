# Matriz de fontes científicas

Atualização: 08/10/2026. Revisão inicial de identificação, trechos metodológicos e código. Não equivale a uma revisão integral nem à validação dos dados. Páginas abaixo são posições no PDF, contando a primeira como 1.

Os originais permanecem locais. Este repositório público contém o catálogo e hashes SHA-256 em `references/manifest.json`, sem redistribuir PDFs ou código de terceiros. Para localizar cada original, use o nome exato no manifesto. Instruções de operação presentes nas fontes são conteúdo documental, não comandos para este projeto.

## Artigos e guia

| ID | Fonte | Localização e evidência | Aplicação e limite |
|---|---|---|---|
| kintner | Paul M. Kintner e Brent M. Ledvina, *The ionosphere, radio navigation, and global navigation satellite systems* | `ASSE_kintner2.pdf`, 20 páginas; figura 8, p. 12, exibe S4 > 0,5 e El > 10° | Critério de seleção dessa análise; não define classe universal de cintilação forte. |
| burrell | Angeline G. Burrell, Nelson A. Bonito e Charles S. Carrano, *Total electron content processing from GPS observations to facilitate ionospheric modeling* | `Burrel2009.pdf`, 13 páginas; resumo, p. 1, trata processamento de TEC e controle de qualidade | Contexto para futura análise de TEC; não fundamenta o mapeamento de colunas .SUM. A primeira página informa publicação online em 24/09/2008; o nome do arquivo não confirma sozinho o ano bibliográfico. |
| depaula | E. R. de Paula, I. J. Kantor e L. F. C. de Rezende, *Characteristics of the GPS signal scintillations during ionospheric irregularities and their effects over the GPS system* | 19 páginas; p. 1 descreve amplitude L1 e 50 amostras/s; p. 5 apresenta S4² = (⟨I²⟩ − ⟨I⟩²) / ⟨I⟩² e cálculo a cada minuto | Fundamenta a definição de S4 e o contexto instrumental do estudo. Não prova que todos os arquivos fornecidos usem essa cadência ou que campo 6 do .SUM seja WBP. |
| malins | J. B. Malins, S. M. White, G. B. Taylor, K. Stovall e J. Dowell, *Modeling the Ionosphere with GPS and Rotation Measure Observations* | PDF Radio Science 2018, 15 páginas; resumo, p. 1, relaciona TEC, modelos de densidade e campo magnético com rotação de Faraday | Referência de contexto para modelagem ionosférica; não define classes S4 nem layout .SUM. |
| cornell-guide | Joanna Hinks, *Cornell Scintillation Simulator: User Guide*, 21/07/2009 | `UserGuide.pdf`, p. 1, separa geração de dados sintéticos e formatação para simulador Spirent | Guia do simulador Cornell, não manual de operações SCINTMON. C/N0 é usado para estimar severidade e não altera a geração descrita pelo guia. |

## Fontes MATLAB: simulação

| Arquivo | Papel identificado | Observação de revisão |
|---|---|---|
| `scintModel04.m` | Geração de histórico complexo com componente Riceana e filtro Butterworth de segunda ordem | Entradas Ts e tau0 em segundos, Nt, K e Nspa; normalização do sinal em alta taxa. Comentário de versão 3 usa Bd = √2·beta0/(π·tau0), mas código usa Bd = beta0/(√2·π·tau0): fator 2 de divergência. Revisar definição de largura de banda e artigo antes de portar. |
| `evalSigmaAndRho.m` | sigma² e rho para modelos Gaussiano, Butterworth e f4 | Cabeçalho referencia Roger Dana (1997) e notas do autor; referências primárias citadas ainda não fornecidas. |
| `estimatePe.m` | Probabilidade de erro de bit DPSK | Usa S4, tau0 e C/N0 em dB-Hz. Tb = 0,02 no código é parâmetro deste modelo, não cadência presumida do .SUM. Depende de `evalSigmaAndRho`. |
| `genUAF2.m` | Exportação de histórico sintético L1/L2 para User Actions File | Não lê .SUM. Conversão de amplitude para dB e fase para metros pertence ao simulador. |
| `guiscint.m` | Interface e parâmetros do simulador | Intervalo de entrada S4 de 0 a 1 é restrição dessa GUI; não justifica excluir observações S4 > 1. Valores iniciais são defaults de simulação, não limiares científicos do projeto. |
| `guivisroll.m` | Visualização móvel de amplitude e fase do histórico sintético | Nome da função declarada é `guivis`, divergente do arquivo. Filtragem de fase usa cutoff 0,2 Hz; não aplicar automaticamente à análise de S4 do .SUM. |

Os arquivos MATLAB foram inspecionados como referência; não foram executados nem validados numericamente. Sua incorporação ou tradução exige esclarecer licença e validar hipóteses e fórmulas.

## Pendências

- Manual SCINTMON: não fornecido; `UserGuide.pdf` não o substitui.
- Arquivos .SUM das quatro noites e plano de trabalho original: não fornecidos.
- Layout e unidades dos campos .SUM, coordenadas e base temporal: não confirmados por este conjunto.
- Conversão LT = UT − 3 h: localizar evidência específica antes de ativar conversão; manter horário bruto por padrão.
- Máscara principal ≥ 30° e classes 0,30/0,60: requisitos do texto de projeto, ainda sem validação contra o plano original; não atribuir aos artigos por inferência.
- Concluir leitura integral, conferência visual de fórmulas/figuras e identificação bibliográfica antes de implementar regras científicas.
