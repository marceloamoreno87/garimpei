# Orchestration Journal — F04 Coleta e acompanhamento de anúncios

**Run:** `2026-11-11T12-13-06Z`
**Feature folder:** `docs/F04-coleta-e-acompanhamento-de-anuncios/`
**Branch:** `master`
**Started at:** `2026-11-11T12:13:06.168752+00:00`
**Retry budget:** `3`
**Status:** `success`

## Escopo autorizado

Implementação e avaliação completas do contrato revisado em 2026-11-11. Retirada aproximada, envio informado com confirmação de destino pendente e janela móvel de 48 horas. F03 está concluída. A sessão privada fornecida pelo usuário poderá ser reutilizada.

## Cycle Log

| # | Kind | Status | Counts / Notes | Artifact |
|---|---|---|---|---|
| 0 | implement-feature | implemented | Janela persistida, cobertura aproximada e consultas nativas verificadas | `impl-report.md` |

| 0 | evaluator | FAIL | 23 PASS · 1 FAIL (`WRK-FONTE-03`) | `eval-report-2026-11-11T13-01-03Z.md` |
| 1 | fix-runner | implemented | Teto 40 → 100; reavaliar no mesmo banco | `operations.md` |

| 1 | evaluator | clean | 24 PASS · 0 FAIL/BLOCKED/MANUAL/SKIPPED · 5 ACs verificados | `eval-report-2026-11-11T14-50-42Z.md` |

## Cycle Detail

### Cycle 0 — implementação → avaliação

Implementação anterior preservada. Ajustes do contrato revisado em execução.

### Implementação e verificações intermediárias

- Janela inclusiva de 48 horas persistida por ciclo; repetição conserva limites. Descoberta exclui datas fora da janela; revisitas a identidades conhecidas continuam.
- Campos opcionais de candidatura e evidência de envio preservam incerteza e leitura de registros antigos. O sentinela histórico 0,0 não gera distância fictícia.
- Consultas reais comprovaram ordenação descendente e fronteira da categoria em cinco páginas. Os parâmetros da URL não prevaleciam sobre o raio salvo de 6 km; o driver passou a enviar centro e raio na consulta nativa de leitura.
- O contexto Comet da requisição foi preservado para manter os IDs iguais aos do detalhe. A regressão de navegador confere os filtros transmitidos e a continuação do servidor.
- Primeira suíte integral: 146 PASS e 1 FAIL; a fixture de edição usava uma publicação futura ao relógio do cenário. Corrigida a data da resposta desse cenário e iniciada a repetição integral. Ainda é preparação da implementação, antes do veredito canônico.
- Seis gates backend aprovados antes dos últimos ajustes; nova execução em andamento. Migrações, check Django, estáticos e quatro testes do harness aprovados.
- Prova real pelo lifecycle iniciada em instância descartável própria, com 40 páginas de proteção, cadência de 1200 ms e intervalo de 60 s. A execução não promove limite de segurança a conclusão da janela.

### Evidências antes da primeira avaliação canônica

- Suíte integral atual: 151 PASS em 306,20 s. Repetição dirigida de limites, cobertura, parser, logs e revisita de anúncios depois das 48 horas: 14 PASS; navegador/união de modalidades: 8 PASS. Seis gates Python novamente aprovados.
- Capturas da jornada executada pelo playwright-cli inspecionadas: janela UTC, carga inicial e estado parcial legíveis; configurações acessíveis e sem sobreposição.
- O primeiro ensaio de lifecycle foi invalidado por uma parada de diagnóstico concorrente com seu controlador privado. Esse ensaio não sustenta conclusão de fonte. Uma nova instância própria passou a executar a passagem contínua.
- O ensaio contínuo de 40 páginas completou as consultas de categoria e retirada, mas a consulta ampliada de produto/envio atingiu o teto antes da fronteira. As leituras de detalhe ainda em andamento não produziram outra falha até o checkpoint 363/448.
- Já há amostras reais de envio declarado em campo estruturado e descrição. A política preserva confirmação do destino como desconhecida.
- Nenhum valor de cookie encontrado nos arquivos candidatos a versionamento; arquivo privado de sessão permanece 0600.

### Cycle 0 — veredito

O worker concluiu a passagem parcial com 444 identidades, 444 observações e 444 eventos initial_load silenciosos. Somente shipping:product:playstation 5 falhou com window_limit. As amostras persistidas incluem 23 ofertas de envio informado. Avaliação completa dos 24 itens: 23 PASS e 1 FAIL. O marco inicial continuou aberto corretamente.

### Cycle 1 — correção dirigida a WRK-FONTE-03

Causa reproduzida: o limite de 40 páginas foi insuficiente para a consulta ampliada de envio. Efeito esperado da correção: permitir até 100 páginas para medir o término real, mantendo parcialidade se esse novo teto ainda impedir a fronteira. A revisão altera configuração, sem redefinir requisitos, interesses ou eventos. A reavaliação conserva o banco e antecipa uma vez next_attempt_at na instância descartável; não altera marco, timestamps da fonte ou relógio UTC.

### Correções do ciclo 1 e controle da reavaliação

O controlador descartável foi corrigido para não antecipar uma tentativa que já estava ativa na inicialização. Uma tentativa de diagnóstico anterior sofreu disputa de sessão e não sustenta a prova final. O banco, identidades e eventos foram preservados. A reavaliação efetiva começou no ciclo 4bc9e155-5b4a-4a29-b344-0c64591a59e3, com janela UTC encerrada em 2026-11-11T13:14:15.903389+00:00.

O teste reproduziu falha na transferência breve do arquivo de sessão; a aquisição agora espera até o timeout, sem abrir contextos simultâneos. Outro teste reproduziu término precoce em página com um item recente seguido por um antigo; a fronteira agora exige página inteira antiga, além da ordenação nativa e monotônica observada. O navegador relê o detalhe completo quando a consulta reutilizada omite a identidade. Regressões: 8 PASS de navegador/consolidação e 14 PASS dirigidos; seis gates aprovados. Requisitos e contrato preservados.

### Decisão adicional e implementação concluída

A medição de 100 páginas concluiu as quatro buscas, mas uma oferta já conhecida havia se tornado indisponível na Meta. A leitura direta confirmou redirecionamento `unavailable_product=1`; não se tratava de credencial rejeitada. Conforme brainstorming, o usuário aprovou explicitamente registrar indisponibilidade e continuar. PRD, spec, plano e contrato foram atualizados preservando os 24 IDs.

Implementado o fato negativo apenas para identidades conhecidas, preservando histórico/referência de preço e excluindo candidatura atual. Falhas técnicas continuam degradando a passagem. Teste PostgreSQL com indisponibilidade e volta passou; a suíte integral atual tem 152 PASS, com 13 aprovações dirigidas adicionais e seis gates aprovados. O marcador terminal nativo SERP_END_OF_RESULTS foi confirmado em ensaio real com a janela anterior fixa: 6/4/11/43 páginas.

A avaliação final efetiva está no ciclo 1701723c-e3eb-454e-9d45-832f8699ccf1, janela encerrada em 2026-11-11T13:47:19.928677+00:00. Nenhum marco, timestamp de fonte ou evento foi alterado manualmente. O reagendamento foi antecipado apenas quando a tentativa anterior já estava finalizada.

### Marco inicial real confirmado

O ciclo 1701723c-e3eb-454e-9d45-832f8699ccf1 concluiu em 2026-11-11T14:03:37.360907+00:00 com 462 observações. As quatro consultas comprovaram a fronteira e a carga inicial permaneceu silenciosa. A oferta 1532605772041551 foi registrada como indisponível, preço atual nulo, histórico preservado e referência de 3800,00; zero eventos de preço derivados dessa observação negativa.

O worker foi parado em 2026-11-11T14:03:40.073823+00:00. A amostra inicial de retirada da categoria não encontrou publicação nova durante dez minutos. O observador foi ampliado às quatro consultas já configuradas, sem escrever anúncios ou eventos no banco. Identificou uma publicação de 2026-11-11T14:11:37+00:00, e o worker reiniciou em 2026-11-11T14:15:22.349602+00:00. O controlador normalizou a comparação entre UUIDs do banco e IDs serializados ao retomar o checkpoint.

A retomada usa o ciclo b2cebb4e-a0fa-4575-90ad-0dba4d017bd0 e janela encerrada em 2026-11-11T14:15:23.914018+00:00. No checkpoint 353/476, não há falhas. A primeira instância de diagnóstico foi encerrada e limpa pelo lifecycle, mantendo a sessão externa intacta.

## Final Verdict

**Status:** `success`
**Completed at:** `2026-11-11T14:59:23.714651+00:00`
**Correções após avaliação:** `1`
**Avaliações canônicas:** `2`
**Commits / push / PR / merge / deploy:** `0`

A avaliação final aprovou os 24 itens e os cinco critérios de aceite. O marco inicial concluiu com 462 observações no ciclo. A retomada completou 472 observações, descobriu dez identidades novas (duas publicações do intervalo de parada), revisitou 15 publicações anteriores à nova janela e conservou marco, UUIDs e eventos, sem duplicação. A indisponibilidade confirmada preservou histórico e referência de 3800,00 sem evento de preço.

152 testes integrais aprovados; após os últimos ajustes de precedência e transporte de proveniência, passaram novamente 13 testes dirigidos, a regressão PostgreSQL de indisponibilidade/retorno e os seis gates. Django, migrações, estáticos e harness aprovados. O exame das oito provas terminais registradas confirmou fronteiras nativas e geografia verificada. A varredura de valores de cookies nos arquivos candidatos a versionamento teve zero correspondências.

**Relatórios preservados:**

- `eval-report-2026-11-11T13-01-03Z.md`: 23 PASS e 1 FAIL no perfil de 40 páginas.
- `eval-report-2026-11-11T14-50-42Z.md`: 24 PASS, status clean.

Os ambientes descartáveis próprios foram encerrados e removidos pelo lifecycle. A sessão externa continua privada, modo 0600. O contexto virtual de categoria da Meta pode incluir resultados relacionados; elegibilidade e entrega não são inferidas a partir da recuperação. Nenhum item permanece pendente nesta avaliação.
