# Avaliação visual e funcional — F19

Aplicada a skill frontend-ui-design com os critérios de `references/criteria.md` e o sistema Mineral de `docs/design/DESIGN.md`. Navegação real por playwright-cli, sessão exclusiva `garimpei-f19`, aplicação própria em15351. Fontes congeladas do ciclo3; nenhum projeto Playwright paralelo foi criado.

| Dimensão | Nota | Evidência observada |
|---|---:|---|
| Design (peso2) |8|Tipografia, fundo mineral, verde escuro e hierarquia editorial seguem o Garimpei; título/causa à esquerda e operação à direita organizam uma tela de utilidade. [Desktop](evidence/ui-final-corrected-desktop.png).|
| Originalidade (peso2) |7|A divisão editorial e linguagem específica de IA local/GPU evitam cards genéricos; a descrição/definições continuam convencionais, adequadas ao propósito.|
| Acabamento (peso1) |8|A360px o conteúdo flui numa coluna, largura documental360=viewport360, sem corte/sobreposição; modelo quebra quando necessário. Botão44,39px de altura; fontes carregadas. [Mobile](evidence/ui-final-resumed-mobile.png).|
| Funcionalidade (peso1) |8|Ação antes dos metadados, pausa/retomada confirmadas; foco visível e skiplink funcionais. Quatorze causas/estados distinguíveis; recuperação incerta não parece análise ativa nem memória liberada.|

Média ponderada `(8×2+7×2+8+8)/6 = 7,67`. Nenhuma dimensão≤3. As notas documentam julgamento visual e não substituem os itens observáveis do contrato.

Jornada por teclado: Tab no skiplink→Enter no conteúdo→Tab no retorno→Tab no botão Pausar(foco solid)→Enter. A resposta confirmou a pausa; a tela ainda mostrou “Modelo residente” antes do descarregamento. Depois da confirmação do serviço mostrou não residente. Retomar pelo botão confirmou intenção e mostrou “IA disponível”; a pausa também persistiu através do reinício anterior. Não houve overlay/menu nesta jornada.

[ui-checks.json](evidence/ui-checks.json) registra geometria, cores, foco, fontes e console0errors/0warnings. Branco no botão verde apresenta contraste≈7,89:1; texto principal no fundo claro≈13,87:1 (cores efetivas registradas no probe). A tela mobile é longa, com metadados abaixo da dobra; a ação principal permanece antes deles e não há área horizontal oculta.

[ui-causes-correction.json](evidence/ui-causes-correction.json) executou14estados pelo navegador e HTTP, com controle persistido e worker próprio pausado, restaurado em finally: serviço/pesos/GPU/VRAM/saída/prazo/incerteza/idle/pausa/drenagem/execução/unloadfailed. As variantes são controladas, sem fingir OOM físico. Resultado anterior ficou visível em todas. Exemplos inspecionados: [execução incerta](evidence/ui-cause-correction-execution_unknown.png), [timeout](evidence/ui-cause-correction-timeout.png), [drenagem](evidence/ui-cause-correction-draining.png), [OOM](evidence/ui-cause-correction-out_of_memory.png).

O finding histórico8PASS/1FAIL foi preservado em `ui-causes.json` e no relatório do ciclo2. Regressão HTTP real com PostgreSQL reproduziu o defeito antes da correção e passou após ela, incluindo timeout e pausa com posse incerta. Não há problema visual acionável pendente nesta avaliação.
