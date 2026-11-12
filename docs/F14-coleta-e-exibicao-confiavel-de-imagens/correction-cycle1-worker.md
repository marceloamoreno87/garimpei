# Ciclo1 — Fluxo contínuo e barreiras do armazenamento

O agendamento anterior emitia20tarefas de uma vez a cada30s, enquanto a exclusividade permitia somente uma aquisição: tarefas sem claim concluíam sem trabalho e aguardavam a rodada seguinte. O worker agora enfileira uma unidade e, ao confirmá-la, enfileira a próxima vencida. `due` retorna vazio enquanto há lease ativa, impedindo encadeamento concorrente em loop. A fila e os estados continuam persistentes, com uma transferência por ambiente e recuperação periódica independente.

Regressão com workerProcrastinate real, origem HTTP local e13originais+13miniaturas: drenagem sem intervalos artificiais de30s,14requisições totais (13fotos+1falha controlada), sem repetição/downloadextra, Cookie/Authorization ou intenção de alerta.1PASS9,94s incluiinit/cleanup. A primeira execução tinha expectativa aritmética incorreta de15assets; observou13/13e a massa foi conferida antes de corrigir somente a expectativa, sem alterar as garantias do teste.

`LocalMediaStore.remove` agora verifica proprietário antes de unlink, inclusive pela fronteira direta. A regressão garante recusa de read/remove/reconcile_orphans por outroenv e integridade dos bytes originais.16testes controladosPASS28,44s na rodada correspondente. Uma captura com manifesto reconhecido começa com completeFalse enquanto obtém os arquivos; source_complete conserva a cobertura declarada pela fonte. A obtenção concluída publica completeTrue apenas quando todas as fotos do recorte estão disponíveis sem limitação.

Gates6PASS em worker-chain-gates.txt. A suíte final da união ainda será executada após sincronização/congelamento. Nenhum contato real foi enviado nesta validação.
