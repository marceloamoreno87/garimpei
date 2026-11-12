# F13 — evidência real de leitura, persistência e interface

**Escopo:** observação somente leitura no principal, aplicação 18351, runtime iniciado pelo coordenador no commit 41e27e5. Nenhum login, clique de retomada, alteração de configuração, reinício ou envio real foi executado pelo curador. Os arquivos originais privados fornecidos pelo coordenador permanecem intactos.

**Resultado honesto:** busca/detalhe, persistência, pausa/retomada e correspondência de interface confirmados. **Continuação ainda MANUAL:** não foi encontrado recibo confirmado da unidade exata derivada de cursor observado. Esta evidência não autoriza marcar F13 done/clean; o avaliador/coordenador decidirá após os gates finais.

## Persistência e retomada

| Leitura UTC | Recibos de navegação | Observações | Tentativas de alerta |
|---|---:|---:|---:|
| 2026-11-12T17:00:51.283791+00:00 | 5 | 6376 | 0 |
| 2026-11-12T17:02:12.117847+00:00 | 23 | 6381 | 0 |
| 2026-11-12T17:17:09.238269+00:00 | 155 | 6444 | 0 |
| 2026-11-12T17:38:52.031731+00:00 · DOM/SQL pausados | 297 | 6510 | 0 |

Na pausa original do coordenador,19 recibos/6380 observações/0 tentativas permaneceram estáveis por 5 s; após SIGCONT avançaram para 23/6381/0. Os14 trabalhos, revisão 2, ciclo e contextos permaneceram os mesmos nas leituras fornecidas. Recibos de navegação incluem unidades de falha; contagens consumidas não são prova de páginas distintas ou continuação bem-sucedida.

O comparador histórico sanitizado confirmou 6365 observações e 2575 eventos originais sem alteração ou perda após migrations/retomada. As tabelas de escolha manual e de alertas tinham zero registros originais neste banco real; a prova não-vazia de preservação desses históricos está no cenário controlado composto, não é inferida de tabelas vazias.

## Correspondência DOM/API/SQL

Uma única pausa adicional, com ownership verificado pelo helper do projeto, durou **1.468 s**. O watchdog de 8 s não disparou; SIGCONT foi enviado em finally. Contagens antes/depois: **[297, 6510, 0]**, estáveis. A sessão própria garimpei-F13-real-proof foi fechada; nenhuma sessão do coordenador foi encerrada.

Os **14/14 artigos** renderizados em /acompanhamento/ corresponderam à API pública e ao SQL no mesmo intervalo pausado: interesse e termo/original por hash, frente, revisão, fase, páginas, detalhes, pendências, buffer e horários. Work/cycle usam SHA256(str(UUID))[:32] na captura e MD5(str(UUID)) nas referências anteriores; o crosswalk verificou exatamente o mesmo conjunto de14 UUIDs e o mesmo ciclo, sem publicar UUIDs crus. Os sete pares contexto/frente também conferiram.

A imagem real-source-dom-sql.png foi examinada. Captura apenas o painel de navegação; rótulos de interesse/termos foram redigidos **depois** da comparação. Contadores, horários, estados e ações permanecem reais. Sem CEP, cookies, JIDs, anúncios/payloads ou cursores crus. A imagem mostra esperas, pendências e cobertura parcial, sem total inventado da fonte.

## Continuação: observação limitada, sem confirmação

A leitura agregada separou **58 unidades de página confirmadas** e **70 unidades de página com falha**. Havia0 recibos de reconstrução nativa confirmada; cursores observados eram numéricos ou ausentes. Os bloqueios agregados incluíam continuation_scope_mismatch, category_unavailable, repeated_page, search_query_template_unavailable e source_request_timeout. Isso informa parcialidade, sem demonstrar uma continuação específica.

Depois, durante **175 s/175 polls**, somente SELECTs observaram checkpoint com cursor, calcularam em memória a próxima unit_key pelo mapper e aguardaram recibo da mesma unidade/revisão, consumed_pages>0, reason=round_robin, sem sufixo:failed:. Foi observada **1 entrada numérica** e **nenhum sucesso correspondente**. Não houve nova pausa, navegação extra ou hipótese perseguida além do limite. O cursor nunca foi exportado; o arquivo contém apenas seu tipo e hash de unidade/contexto/referências opacas.

Por isso, o primeiro bullet de E2E-PERCURSO-01 continua MANUAL quanto à continuação. As demais três verificações reais — interface correspondente, tempos/limites/parcialidade explícitos e ausência de contato/envio — estão observadas. O conjunto de testes controlados continua sendo evidência distinta, sem substituir essa lacuna externa.

## Limites de avaliação

O full combinado500 PASS e três focais finais do coordenador precedem a correção RR de F08; o full final 504/gates ainda era pendente durante esta curadoria. Esta pasta não declara aprovação do patch de F08 nem muda progresso/status final. Alertas estavam desativados e WhatsApp configurado nas leituras, com0 tentativas; sua restauração é responsabilidade exclusiva do coordenador após runtime saudável.

Arquivos relacionados: real-source-dom-sql.json/png, real-source-pause.json, real-source-progress-3.json, real-source-after-resume.json, real-source-progress-4.json, real-source-history-after-migrations.json, real-source-history-after-resume.json, real-source-continuation-aggregate.json e real-source-continuation-observation.json.
