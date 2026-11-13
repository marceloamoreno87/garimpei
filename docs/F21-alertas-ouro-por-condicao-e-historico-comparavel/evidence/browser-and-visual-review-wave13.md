# F21 — avaliação de navegador e design da onda13

Veredito **PASS no escopo controlado**. A prova positiva real E2E-REAL permanece BLOCKED no relatório contratual. Avaliador: agente IA; não houve validação humana independente.

Navegação por `playwright-cli`, sessão própria, aplicação iniciada pelo GoldLab descartável usando `scripts/init.sh`, Django/PostgreSQL reais e I/O sintético explícito. O worker estava intencionalmente pausado no laboratório; seu aviso foi preservado. Não houve envio real nem POST ao fakeWAHA neste percurso.

## Comportamento observado

Lista e detalhe exibem condição, produto normalizado, fotos locais carregadas, composição financeira e cinco comparáveis com preço/data/origem; o aviso informa que preços anunciados não representam vendas. Em1440px há duas colunas no detalhe, e em390px os blocos se empilham sem transbordamento horizontal. Imagem sintética identificada como controle, naturalWidth640.

O caso BASE mostra1900/3000/800. Os casos zero2700/3000/0 e negativo2800/3000/−100 conservam os valores e bloqueiam ouro. A alternância no mesmo relógio expôs seleção antiga de geração/qualificação: e03e829 corrigiu a consulta. As capturas antes da correção estão conservadas para rastreabilidade; o reteste mostrou o motivo atual e nenhuma pronta incorreta. O guard19d3cd8 preserva suspensão de histórico; sua verificação HTTP está no suplemento final integrado.

A injeção de GoldDiagnosticReadFailed só no servidor descartável mantém detalhe200, foto, composição, busca e versão. Na lista, a publicação BASE posterior à negativa produziu Há atualizações. Clicar Atualizar lista manteve q=PlayStation/aba=funcionam/pagina=1, mudou a versão55f2e47b para9e40c868 e exibiu os novos1900/3000/800 com indisponibilidade ouro e sem pronta. Após retirar a injeção e recarregar o mesmo endereço, os filtros/versão permaneceram e a qualificação suficiente voltou. O aviso de canal continua distinguindo pronta de enviada.

O probe WSGI inicial não chamou configure_django e retornou500 numa lista. O Client normal/patchado retornou200; alinhando o bootstrap temporário ao WSGI canônico, o GET live também retornou200. Isso foi erro de montagem do ensaio, sem correção de produto.

## Avaliação visual

| Dimensão | Nota | Evidência |
|---|---:|---|
| Design, peso2 |7|Verde discreto, tipografia escura e hierarquia consistente entre sidebar, foto, composição e referências. Banners superiores ocupam espaço relevante no celular.|
| Originalidade, peso2 |6|Identidade coerente do Garimpei e linguagem de garimpo; cartões e lista de referência continuam convencionais.|
| Acabamento, peso1 |7|Alinhamento e números legíveis, valores zero/negativo explícitos,390px sem corte. Texto do estado do robô fica visualmente próximo do link.|
| Funcionalidade, peso1 |8|Detalhes, retorno e atualização preservam contexto; falha ouro não esconde composição nem afirma envio.|

Ponderada: **6,83/10**. Nenhuma dimensão≤3; sem finding visual crítico. Evidências: ui-gold-detail-desktop-wave13.png, ui-gold-detail-mobile-wave13.png, ui-gold-evidence-mobile-wave13.png, ui-gold-zero-fixed-mobile-wave13.png, ui-gold-negative-mobile-wave13.png, ui-gold-read-error-mobile-wave13.png, ui-gold-read-error-update-mobile-wave13.png e ui-gold-read-recovered-mobile-wave13.png. Dados observados em browser-observations-wave13.json.
