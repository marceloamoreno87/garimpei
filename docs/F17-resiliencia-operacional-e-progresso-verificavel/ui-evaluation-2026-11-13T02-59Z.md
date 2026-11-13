# Avaliação UI F17 — 2026-11-13T02:59Z

Avaliação da superfície UI pelo coordenador com `playwright-cli`, sessão `f17-wave-final`. Não constitui avaliação integral dos 58 itens nem altera o progresso. Laboratório descartável novo, preparado/iniciado por `operations_lab prepare/start` (que usa `init.sh`), seed `counts`, fonte loopback, IA/alertas reais desligados. Viewports 1280×900 e 390×844. Código do snapshot F17 congelado; nenhuma alteração de produto nesta avaliação.

| Item | Resultado | Esperado e observado |
|---|---|---|
| UI-PROGRESS-01 | PASS | Unidade listing com checkpoint confirmado há181s e pendência1 exibiu “Sem avanço recente”, horário/idade181s. Após retomar os workers próprios, `/health/ready` confirmou database/migrations/worker/waha ready, mas a unidade continuou sem avanço: probe técnico não remove estagnação. |
| UI-PROGRESS-02 | PASS | Unidade valuation igualmente antiga com prazo futuro600s mostrou “Aguardando prazo” e próxima tentativa; unidades sem pendência mostraram “Sem trabalho pendente”. |
| UI-PROGRESS-03 | PASS | Counts12/10/8/6/5/4/3/2, foto atual0, definições, instante e revisão1; texto explica sobreposição e não somar. Confirmação no servidor explicitamente não comprova entrega/leitura. Mídia e IA são estágios presentes na base atual, sem trabalho nesta fixture. |
| UI-READING-01 | PASS | Seis cards filtrados por PlayStation mantiveram textContent, ordem e URL completa durante offline real do contexto do navegador. Feedback anunciou falha e hora da leitura válida. Detalhe também conservou rota/filtro/versão e título; retry recuperou na mesma rota. |
| UI-READING-02 | PASS | Publicação explícita gerou revisão93bad1cd enquanto navegador estava offline na971bccdc. Após conexão voltar e “Tentar novamente”, aviso “Há atualizações” apareceu; cards e URL antiga ficaram iguais. Somente Enter em “Atualizar lista” aplicou93bad1cd, conservando q=PlayStation/aba/categoria/página e seis cards. |
| UI-READING-03 | PASS | Parada do PostgreSQL próprio, selecionado por labels de ambiente/checkout, produziu HTTP503 na primeira abertura de `/acompanhamento/`, com erro recuperável e “Tentar novamente”, sem primeira instalação. Banco reiniciado; Enter no retry recuperou mesma rota. |
| UI-BACKUP-01 | PASS | Cópia concluída, falha de exportação sintética e agendamento24h mostraram datas distintas, estado de restauração não testada, exportação explícita e aviso de perda do disco/acesso separado Facebook/WhatsApp. |
| UI-BACKUP-02 | PASS | Registro de exportação interrompida mostrou falha sem link de arquivo pronto. A cópia local foi preservada. Enter em “Exportar esta cópia” gerou outra operação43d63abd, conservando o registro falho e oferecendo download somente da concluída. Download acionado por teclado terminou sem erro. A interrupção de gravação em si pertence à avaliação Worker; aqui a fixture prepara o estado dado. |
| UI-ACCESS-01 | PASS | Tab percorreu navegação, links e ações sem armadilha; foco sólido verde3px. Retomar, retry, aplicar revisão, exportar e baixar acionados por Enter. Estados ocioso/espera/estagnação/suspensão/falha usam texto; falha tem região alert. Larguras client/scroll1280/1280 e390/390, sem overflow horizontal. Nenhum overlay foi aberto ou encontrado nas superfícies exercitadas. |

## Evidências e reprodução

Arquivos `evidence/ui-final-2026-11-13T02-59Z-*`: desktop,390px,estados,backups e503 em PNG, inspecionados visualmente; `status.txt`, `detail.txt`, `final-status.txt` e `readiness.json` registram estado real. Sequência: preparar/iniciar/counts; publicar revisão com `build_publish_exploration().execute()`; suspender rede pelo contexto Playwright; retry; aplicar por teclado; criar unidades sintéticas com `PostgresOperationalRepository` e prazo explícito; criar cópia/registro de exportação falha; desligar/religar somente PostgreSQL próprio; encerrar browser e laboratório. IDs acima são sintéticos e distinguem as revisões desta execução.

Falhas de consulta observadas foram injetadas, além do404 de favicon sem efeito na jornada. Nenhuma credencial, pacote de backup ou perfil do usuário foi incluído. Capturas representam amostra controlada e não certificação geral de acessibilidade. A leitura de cards usa a mesma API textContent antes/depois (comparação inicial innerText/textContent foi descartada por medir representações distintas).

## Julgamento visual

Design7: hierarquia mineral, tipografia e verde consistentes. Originalidade6: textos e funil específicos, composição convencional. Acabamento7:390px legível e sem clipping, com página longa; foco visível. Funcionalidade8: estados e ações verificáveis na jornada. Média ponderada6,83/10. Notas subjetivas não substituem itens do contrato. Melhoria futura: reduzir extensão vertical do diagnóstico sem ocultar definições. Contraste numérico de todos os estados não foi certificado nesta avaliação.
