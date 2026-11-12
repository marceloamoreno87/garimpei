# F02 — Fix-runner, ciclo 1

Entrada: eval-report-2026-11-10T20-54-37Z.md. Itens: E2E-LIMPEZA-01 e E2E-ISOLAMENTO-01. Causa: --clean não removia redes Compose exclusivas; execuções repetidas esgotaram os pools do daemon. Efeito esperado: liberar rede própria descartável e preservar redes/recursos alheios.

Reprodução: tests/lifecycle/test_network_cleanup.py falhou no código anterior porque network inspect retornou 0 após --clean. Após a correção, esse teste e os oito cenários de falha de início/ferramenta passaram (9 PASS em 26,18 s). Seis gates Python aprovados na árvore corrigida.

Alterações: labels de instância/checkout para a rede Compose; consulta e validação de projeto, labels e endpoints; validação antes de reutilizar/remover rede; remoção da rede própria na limpeza. Fixtures negativos encerram suas redes após verificação. Regressão confirma rede estrangeira intacta. Arquivos: compose.yaml, infra/runtime/{containers,lifecycle}.py, tests/lifecycle/{test_network_cleanup,test_startup_failures}.py e documentação operacional. Nenhuma mudança de requisito/contrato/spec/plano. Sem commit.

As 28 redes legadas desta própria execução foram removidas individualmente com evidência de nome/projeto, data após início F02 e ausência de endpoints; artefato preservado na avaliação inicial. Sem prune global. Reavaliação integral pendente; este relatório não declara done.
