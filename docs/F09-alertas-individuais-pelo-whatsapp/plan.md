# F09 — Plano de implementação de alertas individuais pelo WhatsApp

**Pré-requisitos**

- F04, F05 e F07 avaliadas e integradas. Confirmar feed e observação da F04, condição efetiva da F05 no corte do evento e avaliação financeira da F07 para a mesma observação.
- Ambiente descartável da F02 com PostgreSQL e worker Procrastinate. Reusar a imagem GOWS e preparar o WAHA local programável, as fixtures e o relógio descritos no [contrato](contract.md).
- Para a prova real, preparar conta, sessão persistente, API key e um destinatário individual autorizado. Confirmar o procedimento de pareamento e recuperação no volume próprio. Dados privados ficam fora do repositório.

### Etapa 1 — Interfaces e prova de viabilidade

**1. Fechar os contratos entre features.** Confirmar ordem dos eventos, leitura da classificação no corte de publicação e identificação da composição financeira por observação. Preparar as extensões aditivas necessárias.

**2. Verificar o WAHA/GOWS da fundação.** Comprovar envio de texto, identificação da conta e do destino, leitura de ACK e busca de referência no chat. Registrar o perfil operacional e suas limitações.

**Verificação da etapa** — Exercitar as interfaces em base com histórico e produzir as evidências do item `E2E-WHATSAPP-01` no ambiente autorizado assim que o fluxo de envio estiver disponível. A prova de API pode ser feita antes com uma mensagem sintética ao mesmo destinatário de teste.

### Etapa 2 — Consumo durável e elegibilidade

**3. Adicionar persistência e consumo do feed.** Preservar a posição de consumo e as decisões por evento, com retomada após falha de leitura ou gravação.

**4. Resolver elegibilidade pela versão do evento.** Aplicar as regras para descobertas, reduções, silêncio, cobertura, classificação e lucro. Preservar a dependência de um envio anterior nas reduções e a revalidação antes de despachar.

**Verificação da etapa** — Aplicar a migração em banco novo e em banco com dados das dependências. Executar `WRK-ELEGIBILIDADE-*`, `WRK-RETOMADA-*` e `E2E-CLASSIFICACAO-*`.

### Etapa 3 — Despacho e reconciliação

**5. Integrar a configuração privada e o adapter WAHA.** Montar uma mensagem por evento elegível, verificar sessão e destino e registrar tentativas antes do efeito externo.

**6. Recuperar tentativas sem duplicar mensagens.** Reagendar falhas comprovadamente seguras e reconciliar tentativas de resultado incerto pelo histórico do provedor.

**Verificação da etapa** — Executar `WRK-ENVIO-*`, com reinício, falha de sessão, perda de resposta e retorno tardio. Confirmar transições duráveis e contagem de POSTs da fonte de teste.

### Etapa 4 — Operação e aceite

**7. Documentar a operação local.** Registrar configuração, pareamento, leitura dos diagnósticos, conservação do volume, recuperação de histórico e limites da confirmação.

**8. Executar gates e fechar o contrato.** Verificar o fluxo real com a imagem e o destino autorizados. Registrar as medições do perfil e as evidências por critério do PRD.

**Verificação da etapa** — Executar os gates e todos os itens do [contrato](contract.md), incluindo a prova real de envio e recuperação do recibo no WAHA.
