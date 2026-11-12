# Inicialização e rollback dentro do orçamento observado

Base: `61441933dac69b94d644a0f44d3a6002791504e1`. Branch `fix/startup-deadline-envelope`, worktree isolada `6cd6`. Reprodução e validação usam cópias descartáveis da aplicação, com portas/bancos próprios, fonte sintética e remoção somente depois de conferir labels de ambiente/checkout. Nenhuma mudança no candidato congelado `a716`, instalação principal, script ou configuração.

## Defeito demonstrado

Com startup8s/shutdown1s, a falha WAHA reproduziu8,031603s; a execução instrumentada chegou a8,046440s. O relógio começava em `_start_attempt`, depois de0,491048s de shell/uv/imports. O loop aguardava0,2s sem limitar ao tempo restante e começou o rollback0,127210s depois do deadline. Processos consumiram0,252082s e Docker1,055942s, além das inspeções/finalização. A reserva fixa2s já não cobria o conjunto. Cada parada ainda recebia prazo novo, e a requisição HTTP podia começar com timeout3s perto do fim da janela.

[Reprodução](waha-before.txt), [marcos temporários](waha-timing-before.txt) e [resumo numérico](timing-summary.json). A instrumentação `PERF` foi removida do código final.

## Correção

O envelope monotônico começa em `start`, antes das inspeções. Uma reserva explícita1s cobre entrada/retorno medidos; a fase de preparação reserva até metade do orçamento para rollback, calculado por uma graça compartilhada de processos, uma graça de Docker e0,5s para inspeções/manifesto. Operações de Docker/Compose recebem o restante dessa mesma janela. Esperas e HTTP usam o restante, e não confirmam prontidão depois do prazo. A sondagem autenticada não inicia outra tentativa no trecho menor que seu limite de conexão2s.

Rollback usa um prazo compartilhado entre os processos; tempo usado por um não é concedido novamente ao seguinte. Inspeções e parada Docker usam o mesmo prazo final. A graça `docker stop --time` também é reduzida quando o restante é menor, preservando a verificação de ownership. O caminho de parada normal conserva sua graça configurada, preservação de volumes/sessão e diagnóstico de conclusão desconhecida quando precisa matar um processo.

## Verificação

- Seis gates Python aprovados, exit0,425 arquivos de produção: [gates.txt](gates.txt).
- Todos os36 testes lifecycle passaram em95,77s: [execução](lifecycle-after.txt) e [inventário](lifecycle-inventory.txt).
- Falha PostgreSQL:3,817729s. Falha WAHA:6,391843s. Imagem inválida:1,043685s. Todos dentro dos8s originais, com retorno1, ausência de Ready, canary não exposto e nenhum contêiner próprio em execução.
- Permanecem os cinco cenários de ferramentas ausentes. A suíte também prova starts saudáveis com timeout padrão, locks, PID/porta/rede estrangeiros preservados, recusa de limpeza não autorizada, retenção de dados/sessão, rollback parcial com PostgreSQL preexistente e migrations.
- `assert elapsed <= 8` e todas as verificações de ausência de Ready/canary/containers foram mantidos; só foi acrescentada a impressão do elapsed para diagnóstico.
- Ruff/diff sem erro; nenhum envio ou acesso real de Facebook/WhatsApp.

## Limites

A reserva1s inclui a entrada shell/uv/imports e saída no ambiente medido. Ela não é um hardcap para um `uv sync`, preflight, import ou operação de sistema arbitrariamente bloqueados, nem uma garantia formal diante de suspensão do processo/OS. O escopo aprovado pelo coordenador é corrigir o orçamento observado com folga e rollback real, preservando os contratos; scripts, env e supervisor externo não foram ampliados. A suíte completa da união posterior e a integração na master pertencem ao coordenador.
