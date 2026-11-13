# F10 — Configurações de integrações

<!-- current-execution:start -->
> **Situação em 2026-11-13:** `done` — [avaliação registrada](eval-report-2026-11-11T21-54-20Z.md); o [progresso canônico](../prd_progress.json) conserva ciclos e datas.
> Menções à feature ainda não iniciada ou à ausência do scaffold refletem a elaboração original. Consulte o [estado consolidado](../status-atual.md) para implementação e limites atuais. Evoluções explícitas do PRD e contratos posteriores prevalecem nos pontos alterados; IDs e evidências históricas são preservados.
<!-- current-execution:end -->

Requisito atual do usuário: adicionar cookies do Facebook pelo Garimpei, avisar quando expirarem e disponibilizar conexão WhatsApp e escolha de grupo no menu. Extensão autorizada de F04/F09; preserva regras de elegibilidade e não altera recibos antigos. A restrição anterior de destino direto da F09 passa a admitir um grupo escolhido pelo usuário. Um alerta continua sendo uma mensagem por evento.

## Fluxo

Uma área Integrações acessível em todas as telas permite colar cookies como cabeçalho Cookie ou JSON exportado/estado Playwright. Validar c_user/xs e domínios Facebook; nunca reapresentar o conteúdo. Salvar em diretório privado externo ao checkout, com permissões restritas e arquivo por revisão. Salvar não comprova sessão ativa: mostrar “Aguardando verificação” até coleta válida. Cookie com expiração conhecida vencida é rejeitado; ausência de expires não permite inventar validade. Ao detectar login exigido/expiração, suspender a coleta e mostrar aviso persistente com ação Renovar cookies; checkpoint/challenge exige confirmação no Facebook. Trocar cookies invalida gerações de coleta antigas e retoma o monitoramento com o mesmo marco inicial e histórico.

WhatsApp usa WAHA local autenticado. Conectar inicia/cria a sessão própria (default se não houver configuração anterior), apresenta QR pelo backend e acompanha estado. Em WORKING listar grupos com paginação e parser GOWS (JID/Name) e formato normalizado (id/subject/name). Salvar verifica novamente conta e participação no grupo; seleciona exatamente um grupo e opção explícita de ativar alertas. Falha/lista vazia exige recuperação na tela, sem inventar conexão. Desativar alertas não apaga recibos nem sessão. Nenhuma mensagem de teste é disparada ao conectar ou escolher grupo.

## Organização e consistência

Domínio integration: cookies, estados, grupo e portas tipadas. Casos de uso salvam sessão, consultam conexão, iniciam pareamento e configuram destino. Infra: arquivo privado/metadata PostgreSQL, gateway WAHA, forms/templates e contexto de aviso. Composição explícita em main.py; env.py resolve diretório privado e overrides legados. Migração aditiva após 0008. Configuração via UI prevalece quando existente; env permanece compatível para instalações anteriores e cenários F09. Worker consulta revisão atual por tarefa, sem reiniciar para renovar cookie/destino. Sessões antigas não sobrescrevem o novo arquivo. Vinculação e reconciliação F09 continuam fixas por intenção; grupos são validados pelo ID canônico e evidência de saída/conta do engine.

Interface amplia o layout Mineral existente, com seções Facebook/WhatsApp, estados claros, erros associados, CSRF, cache no-store e sem segredos em logs ou snapshots. QR é exposto somente na rota local, sem chave na URL. Documentar e verificar pelo navegador desktop/janela estreita com dados sintéticos. Conta real e cookies reais são fornecidos apenas pelo usuário na aplicação.

## Apresentação atual — 2026-11-13

Menu e cabeçalho identificam Integrações; avisos seguem a seção, campos avançados permanecem em disclosure e polling respeita foco e aba oculta. Veja as [convenções da interface](../design/implementation.md), a [auditoria original](../design/audit-2026-11-13/README.md) e a [verificação integrada](../design/audit-2026-11-13/integration-master.md). Este complemento preserva IDs e critérios do contrato original.
