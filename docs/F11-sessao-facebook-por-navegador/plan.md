# F11 — Plano

1. Diagnosticar estado atual sem ler cookies nem repetir acesso bloqueado; registrar decisão do usuário.
2. Reproduzir parâmetros incorretos de cookies da UI com regressão; resolver padrões na configuração central depois de definir o tipo de sessão.
3. Persistir solicitação/status por migration aditiva e invalidar gerações de coleta sob lock de publicação.
4. Abrir perfil privado persistente com navegador visível; manter um dono no worker, confirmação explícita, verificação, gravação e fechamento antes da retomada.
5. Integrar comandos/feedback no menu; conservar importação avançada e histórico. Testar CSRF, sessão inválida, reinício/desafios, persistência real em Chromium e interface estreita.
6. Executar gates, checks e regressões afetadas; deixar app rodando e login real para o usuário. Não concluir eficácia contra detecção por testes sintéticos.
