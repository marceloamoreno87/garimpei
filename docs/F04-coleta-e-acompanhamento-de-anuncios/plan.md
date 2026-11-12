# F04 — Plano de implementação de coleta e acompanhamento de anúncios

**Pré-requisitos**

- F03 avaliada e integrada, com leitura da configuração confirmada e catálogo local. F02 operacional com os componentes e versões registrados em [versions.md](../F02-fundacao-tecnica-e-ambiente-local/versions.md). Subir o ambiente descartável conforme [operations.md](../F02-fundacao-tecnica-e-ambiente-local/operations.md).
- Preparar as fixtures, relógio controlado, entradas de geografia e sequências da fonte previstos no [contrato](contract.md). Usar `playwright-cli` para verificar a rota de acompanhamento.
- A validação com fonte real depende de condições de acesso documentadas, dos parâmetros medidos e de um CEP de teste resolvível. Preparar navegador/sessão conforme a prova de acesso e guardar arquivos privados fora do repositório. O trabalho local pode avançar com fixtures enquanto essas dependências são investigadas.

### Etapa 1 — Viabilidade da fonte e recorte operacional

**1. Verificar operações e cobertura.** Verificar acesso autorizado, buscas por categoria e por produto, contexto geográfico, continuação, detalhe e evidência de entrega no CEP. Validar centro e raio aproximados realmente aplicados na conta. Verificar os campos de envio informado e seu alcance territorial, mantendo confirmação do CEP separada. Substituir as recusas incondicionais do adaptador por verificações observáveis.

**2. Fixar o perfil do coletor.** Usar a janela aprovada das últimas 48 horas. Comprovar filtro temporal ou ordenação e continuação que permitam encerrar essa janela. Registrar cadência, tempo por passagem e teto de segurança com base nas medições. Atingir o teto antes da fronteira temporal mantém a passagem parcial.

**Verificação da etapa** — Reproduzir `WRK-FONTE-01` a `WRK-FONTE-03`, com evidência sanitizada, timestamps, janela e parâmetros. O aceite da etapa depende da fonte real.

### Etapa 2 — Dados e regras de acompanhamento

**3. Criar o módulo de anúncios e a migração aditiva.** Preparar a persistência de identidade, observações, interesses, marcos e eventos sobre a base existente da F03.

**4. Implementar correspondência, cobertura e histórico.** Produzir leituras tipadas para os consumidores, incluindo localização aproximada, envio informado, confirmação do destino, pertencimento à janela e estado de atualização. Persistir os limites UTC de cada ciclo. Ler observações anteriores com a incerteza adequada quando esses qualificadores estiverem ausentes.

**Verificação da etapa** — Aplicar a migração em base nova e sobre uma base F03 configurada. Executar os cenários de `Service` e `Event` do contrato com entradas determinísticas.

### Etapa 3 — Coleta recorrente e recuperação

**5. Integrar a fonte e as buscas ao worker.** Compor os adaptadores e a leitura da F03. Fazer a carga inicial terminar após comprovar e gravar a janela de 48 horas do escopo vigente, admitindo candidatos com localização aproximada ou entrega no CEP a confirmar.

**6. Integrar agenda e retomada ao lifecycle da F02.** Recuperar ciclos interrompidos conservando seus limites de janela. Em um novo ciclo, recalcular as últimas 48 horas e revisitar os anúncios conhecidos, inclusive os mais antigos. Reconciliar o escopo e preservar identidades, preços e silêncio da carga inicial.

**Verificação da etapa** — Exercitar `WRK-COLETA-01` a `WRK-COLETA-10`, incluindo interrupção antes e depois do marco, acesso parcial e execução concorrente. Confirmar que a fila técnica da F02 segue operacional.

### Etapa 4 — Acompanhamento e integração

**7. Apresentar o estado persistido da coleta.** Atualizar a tela de acompanhamento da F03 para refletir o primeiro ciclo, a continuidade e falhas reais. Manter a jornada da configuração guiada e o acesso às preferências.

**8. Fechar a validação das superfícies.** Executar os gates, percorrer a jornada integrada e registrar evidências por item e por critério de aceite. Associar os resultados reais da fonte ao perfil efetivamente usado.

**Verificação da etapa** — Conferir os itens `UI-ACOMPANHAMENTO-*`, `E2E-CONFIGURACAO-*` e todos os gates do [contrato](contract.md). Confirmar os cinco critérios da F04 e as interfaces de integração sob sua responsabilidade.

## Sequência de validação após a revisão de 2026-11-11

1. Reproduzir os bloqueios atuais de geografia incondicional, envio recusado e limite de páginas.
2. Verificar dados reais de filtros, envio e datas, com sessão privada e evidência sanitizada. Demonstrar a semântica das 48 horas antes de usá-la para concluir a janela.
3. Cobrir posições aproximadas e origem indisponível, envio anunciado sem confirmação do CEP, fronteira exata de 48 horas, data ausente, anúncios promovidos e resultados fora de ordem. Manter cobertura de histórico, concorrência e falhas de persistência.
4. Completar uma carga inicial real com a nova política e observar somente eventos silenciosos.
5. Registrar uma parada, retomar no mesmo banco e verificar uma publicação recuperável da interrupção dentro das 48 horas, junto da atualização de anúncios conhecidos e da ausência de duplicação.
6. Executar gates e a avaliação completa do contrato. Associar o novo relatório à entrada F04.

Os relatórios e o progresso existentes registram a execução anterior. A revisão das regras exige implementação e reavaliação antes de concluir F04.

### Ajuste aprovado durante a execução

Distinguir confirmação explícita de indisponibilidade de falha técnica. Persistir o estado para identidades já acompanhadas, preservar referência de preço e histórico, excluir a oferta das candidaturas atuais e permitir concluir a passagem. Validar em PostgreSQL uma carga inicialmente parcial, a indisponibilidade confirmada antes do marco e a volta com redução de preço. Na fonte real, conferir a evidência vinculada ao ID e repetir a passagem e a retomada no mesmo banco.
