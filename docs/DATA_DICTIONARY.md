# Dicionário da tabela canônica

| Campos | Significado e unidade |
|---|---|
| source_file, station, night | Arquivo, nome do cabeçalho e noite (data do cabeçalho) |
| line_number, block_id | Linha física e bloco; não são chave para remover observações |
| datetime_raw, time_raw_hhmm, observation_date | Hora/data brutas, preservadas; data avança em 23:xx → 00:xx |
| datetime_utc, datetime_local, input_time_basis, local_utc_offset_hours | Tempo convertido apenas sob opção explícita; offset fixo em horas |
| prn | Identificador de satélite fornecido |
| x_sat_raw, y_sat_raw, z_sat_raw, receiver_x/y/z | ECEF bruto; unidade ainda não confirmada documentalmente |
| raw_5, raw_7, raw_9, raw_10, block_aux_raw | Campos preservados sem interpretação física |
| signal_power_raw | Potência/informação de sinal, unidade não confirmada; não rotular C/N0 ou SNR |
| original_line, header_aux_raw (tabela stations) | Proveniência textual |
| station_unit, satellite_unit, coordinate_unit_inferred | Unidade escolhida/inferida e flag; estado registrado por observação |
| station_latitude_deg, station_longitude_deg | Latitude geodética/longitude WGS84 em graus |
| east_m, north_m, up_m, range_m | Vetor de visada ENU e distância em metros |
| azimuth_deg, elevation_deg, quadrant | Azimute/elevação em graus e quadrante geográfico; azimute indefinido vazio |
| geometry_valid | Geometria calculada; ausente/falha não significa elevação zero |
| passes_mask_10, passes_mask_30, passes_active_mask | Flags geométricas; não removem linhas |
| passes_active_selection | S4 válido, máscara ativa e critério S4 do perfil quando aplicável |
| s4, s4_valid, s4_above_one | Índice adimensional, validade e inspeção acima de 1 |
| s4_class_project, s4_class_active | Classificação principal e do perfil ativo; Kintner é seleção |
| s4_gt_03, s4_ge_03, s4_gt_05, s4_ge_06 | Flags de comparação com operadores explícitos |
| exact_duplicate, excluded_exact_duplicate | Duplicata marcada; exclusão opcional apenas no recorte, original mantido |
| kp, dst, geomagnetic_condition, geomagnetic_source | Kp (índice), Dst (conforme fonte, esperado nT), classificação e proveniência |
| f107, sunspot_number, solar_cycle_class, solar_source | Índices e classificação fornecidos; unidade F10.7 deve acompanhar a fonte (tipicamente sfu) |
| solar_cycle_period_from_plan | Classificação apenas por ano do requisito; não é medição solar |

`parser_diagnostics` contém arquivo, linha, tipo_problema, conteudo_original e acao_tomada. As tabelas `stations`, completa e diagnósticos mantêm os metadados do arquivo para auditoria. Parquet conserva o esquema; CSV usa campos vazios para contexto/geometria ausente.
