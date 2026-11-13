# F11 — Sessão Facebook por navegador

<!-- current-execution:start -->
> **Situação em 2026-11-13:** `done` — [avaliação registrada](eval-report-2026-11-11T21-54-20Z.md); o [progresso canônico](../prd_progress.json) conserva ciclos e datas.
> Menções à feature ainda não iniciada ou à ausência do scaffold refletem a elaboração original. Consulte o [estado consolidado](../status-atual.md) para implementação e limites atuais. Evoluções explícitas do PRD e contratos posteriores prevalecem nos pontos alterados; IDs e evidências históricas são preservados.
<!-- current-execution:end -->

Decisão do usuário: janela própria com login manual e coleta automática, em substituição à cópia habitual de cookies. Perfil privado dedicado, distinto do navegador pessoal; login e desafios resolvidos pelo usuário na janela. O perfil mantém cookies e armazenamento local entre execuções. Isso não promete impedir detecção nem superar um bloqueio da plataforma.

O menu Integrações permite abrir a janela, acompanhar abertura/espera, confirmar o login e verificar acesso ao Marketplace. A confirmação exige sessão autenticada, não apenas fechar a janela. A coleta fica suspensa durante login, falha, interrupção e desafios. Um único dono utiliza o perfil por vez; parada normal conserva o perfil e reinício não libera um acesso suspenso. Ofertas, marcos iniciais e recibos não são apagados. Cookies importados continuam como opção avançada de compatibilidade, com os mesmos parâmetros padrão do acesso real.

O worker existente mantém a janela de login por até 15 minutos. A interface persiste comandos e status, sem senha, cookies ou tokens na resposta. Verificação bem-sucedida fecha e grava o perfil antes de retomar a coleta. As coletas reutilizam o mesmo diretório e usam navegador visível. O processo continua sendo automatizado; desafios exigem ação humana e nenhuma tentativa de bypass integra esta mudança.

Dependências F04/F10 implementadas, com pendências reais anteriores preservadas. A nova instrução autoriza a extensão antes do aceite externo F09/F10. Ambiente WSLg disponível. Login real exige a participação do usuário; provas locais usam apenas origem HTTP loopback isolada de avaliação.

## Apresentação atual — 2026-11-13

O aviso de acesso compartilhado foi compactado e contextualizado. Polling não substitui a área enquanto o usuário interage; login, sessão e suspensão mantêm as regras aprovadas. Veja as [convenções da interface](../design/implementation.md), a [auditoria original](../design/audit-2026-11-13/README.md) e a [verificação integrada](../design/audit-2026-11-13/integration-master.md). Este complemento preserva IDs e critérios do contrato original.
