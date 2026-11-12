# Correção dirigida — ciclo 1/3

Relatório de entrada: `eval-report-2026-11-12T14-35-31Z.md`, gate Suíte. O full terminou com 2 FAIL / 29 PASS após SIGINT próprio, exit 2. Os 440 arquivos congelados mantiveram exatamente o conjunto e os hashes até a saída; fixtures próprias encerradas antes das edições.

| Falha reproduzida | Causa | Correção e garantia |
|---|---|---|
| window_proofs vazio no histórico de 48 h | A fonte valida end/empty, mas não fornece texto window_proof; F13 perdeu o fallback source_exhausted existente. | Restabelecer prova no término validado. Continuação, diagnóstico e identidade inválida não recebem prova de fronteira. O teste original passou sem alteração. |
| Restart espera nova busca e proíbe detalhe | Estratégia anterior reconstruía pesquisas; F13 persiste a página e candidatos pendentes. | Com autorização, o teste exige exatamente cinco detalhes 220–224, nenhuma nova busca, snapshots integrais dos 20 registros anteriores e total final 25. |
| Publicação anterior ao bloqueio de outro interesse exige duas observações | Estratégia antiga esgotava alvos antes de alternar. Justiça F13 publica uma observação e concede turno à segunda categoria. | Com autorização, exigir publicação útil e ID101 já visível antes de liberar cameras; manter silêncio, quatro observações finais, detalhe101 único e dois matches. |
| Teste de adoção da política usa ORM atual contra schema0012 | CollectionState atual seleciona source_not_before, coluna introduzida depois. | Com autorização, ler CollectionState histórico de project_state0012; manter cutover, marco, eventos e recibos, e restaurar migrations antes de voltar ao ORM atual. |

RED focal: dois testes falharam em 23,47 s com estado público capturado. O contador window_proofs era zero, sem alias adicional. As chamadas após restart eram apenas /cep e /detail/220 até /detail/224. GREEN isolado da janela48h: 1 PASS em 10,55 s. A execução completa do módulo e os gates posteriores constam do diário e do relatório final; este documento não antecipa seus resultados.

Não houve alteração de requisito, remoção de assertions de negócio, xfail ou dispensa de gate. Nenhum arquivo comum foi editado por esta frente durante a correção. A prova Facebook real permanece MANUAL conforme instrução do usuário.

## Verificação concluída

Módulo histórico completo:13PASS em169,66s. Gates Python, Django, migrations e build:exit0. Suíte ampla:443PASS em1425,39s, exit0, sem mudanças dos440arquivos congelados. Resultado canônico:19PASS/1MANUAL; a pendência é somente a prova real adiada.
