# Regras científicas e hipóteses

`config/scientific_rules.yaml` é o registro central, em sintaxe JSON compatível com YAML 1.2. Cada entrada contém valor, unidade, finalidade, fonte, estado de confirmação e nota metodológica. A interface permite expandir cada regra. O pacote ZIP inclui o registro e todos os parâmetros ativos.

## Perfis

- `project_default`: fraca S4 <0,30; moderada 0,30 ≤ S4 <0,60; forte S4 ≥0,60. Elevação ≥30°. Origem: requisitos fornecidos; plano original pendente.
- `kintner_fig8`: S4 >0,5 e elevação >10°, ambos estritos. Critério de seleção da figura 8, PDF p. 12; não produz classes fraca/moderada/forte.
- `custom`: dois limites crescentes e elevação definidos pelo usuário. Dois limites determinam três classes; não introduzimos intervalos sem classificação. Estado explícito: critério personalizado, sem correspondência publicada garantida.

S4 inválido (negativo/não finito) permanece na tabela completa, excluído das estatísticas válidas. S4 >1 permanece válido e marcado. S4 não é recalculado da potência. Frações usam somente observações com S4 válido; as comparações ≥0,30, >0,50 e ≥0,60 são preservadas sem arredondar antes da seleção.

## Geometria e unidades

WGS84 é uma hipótese de datum do projeto; não confirma o datum do instrumento. Valores do elipsoide vêm da NGA. A inversão de ECEF implementa iteração de latitude; testes independentes com PyProj verificam 1e-8 grau e 1e-3 metro. Latitude/longitude manuais da CLI básica continuam disponíveis. Inferência por magnitude é registrada, nunca apresentada como unidade documentalmente confirmada. Magnitude fora dos intervalos exige seleção manual. A inferência de satélite é por observação, permitindo diagnosticar escalas incoerentes.

O alerta de localização usa uma caixa regional ampla configurada em `app_config.yaml`; é heurística, não posição oficial. Ele não desloca a estação. Zênite/nadir têm quadrante vazio; pontos abaixo do horizonte ficam no conjunto completo.

## Tempo

`raw` preserva a base desconhecida. Em `utc`, assume-se explicitamente que o horário do arquivo é UTC; em `local`, que é local no offset fixo escolhido. UTC/local nunca são inferidos da hora do arquivo. Offset −3 h é requisito, ainda pendente de confirmação específica; não modela horário de verão histórico. A noite é a data do cabeçalho, distinta da data da observação após meia-noite.

## Contexto

Sem CSV fornecido, Kp, Dst, F10.7 e número de manchas ficam ausentes. Kp ≤3 é critério calmo do texto do projeto; Kp >3 não é automaticamente tempestade. A classificação temporal máximo 2001–2002 / mínimo 2008–2010 é campo separado com sufixo `from_plan`; não mede F10.7 nem substitui contexto.

## Estatística

Desvio padrão amostral (ddof=1), indefinido para N<2. P90/P95 usam interpolação linear de Pandas. Estes são critérios computacionais documentados, não novos limiares físicos. Máximo empatado: primeira observação na ordem original. As frações descrevem a amostra, não probabilidade universal ou relações causais. Seleção do perfil Kintner restringe a amostra e portanto altera os denominadores; filtros são registrados em todos os produtos.

## Fontes pendentes

Manual SCINTMON, plano original e quatro arquivos .SUM reais. O simulador Cornell não substitui observações nem o manual. A divergência de largura de banda nos arquivos MATLAB permanece registrada; nenhuma simulação foi portada como resultado observacional.
