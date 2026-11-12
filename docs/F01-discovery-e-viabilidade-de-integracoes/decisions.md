# F01 — Registro da escolha e pendências

Data de atualização: **2026-11-10 UTC**. Discovery original: run `2026-11-10T19-07-31Z`; prova prática e decisão do usuário complementadas nesta data.

## Escolha final

| Campo | Estado |
|---|---|
| Estado | **aprovada** — escolha de plataforma e direção inicial de acesso. |
| Plataforma aprovada | **Facebook Marketplace**, primeira integração do MVP. |
| Estratégia de acesso aprovada | Páginas de busca/detalhe por navegador, inicialmente sem login, conforme prova prática. Biblioteca e implementação definitiva do coletor ainda por especificar. |
| Data da decisão do usuário | 2026-11-10. |
| Referência à decisão | E-PS5-DEC-01: mensagem nesta conversa, após os testes: “vamos de facebook e se precisar posso passar o cookies pra acessar os detalhes”. |
| Condições aprovadas | O usuário disponibilizará cookies/sessão se o acesso aos detalhes exigir autenticação. Nenhum cookie foi solicitado ou recebido; os detalhes da amostra funcionaram sem login. Solicitar arquivo privado de sessão fora do repositório somente se necessário. Nenhuma redução de requisito aprovada. |
| Efeito no progresso | Pendência de escolha L-08 resolvida. F01 reavaliada integralmente com 14 PASS e gates do harness aprovados em [eval-report-2026-11-10T19-53-58Z.md](eval-report-2026-11-10T19-53-58Z.md); progresso `done`. A passagem para F02 está liberada pela avaliação, sem tomar a escolha isoladamente como conclusão. |

A aprovação vem da mensagem explícita do usuário acima, após a recomendação e a prova prática. Não depende da aprovação anterior da stack nem do pedido original de execução da F01. Aprovar a fonte não comprova automaticamente estabilidade, geografia, frete ou cobertura integral do MVP.

## Recomendação apresentada para decisão

**Complemento posterior em 2026-11-10:** o usuário solicitou testes reais das buscas por PlayStation 5 em OLX, Facebook e Enjoei. A [prova prática](probe-playstation5-2026-11-10.md) encontrou busca/detalhe sem login em Facebook e Enjoei, continuação nas duas fontes e bloqueio Cloudflare 403 em OLX. A recomendação foi **priorizar Facebook Marketplace para o foco local em usados em São Paulo**, mantendo Enjoei como alternativa e OLX dependente de diagnóstico. Isso é inferência condicionada à amostra, sem estabilidade, raio de 20 km ou frete no destino comprovados. O usuário aprovou Facebook na mensagem E-PS5-DEC-01; a sugestão abaixo fica preservada como histórico da investigação documental original.

**Sugestão condicionada:** investigar primeiro **OLX**, por **páginas de busca/detalhe sem sessão inicialmente**, validando possibilidade de extração e condições de acesso antes de adotar a estratégia. Nenhum coletor/ferramenta escolhido ou instalado. A API de inventário documentada não é tratada como busca geral. Motivos, alternativas e evidências: [report.md — Recomendação](report.md#recomendação-condicionada-e-próximos-passos), E-OLX-01/02.

Condições que a PoC precisa resolver: acesso estável, categorias/subcategorias e nome/modelo, campos/identidade, retirada SP em 20 km, entrega no CEP privado, origem do frete, janela recuperável, amostra de usados/novos, limites/custo/recursos. São questões em aberto, não exceções já aceitas. Mercado Livre é alternativa se comprovar acesso elegível e cobertura; Enjoei/Facebook continuam alternativas com lacunas. Nenhuma candidata demonstrou todos os requisitos nesta execução.

A escolha final está registrada acima. Contrato F01 reavaliado integralmente antes da implementação F02, conforme relatório acima. Lacunas obrigatórias precisam de consequência e resolução, sem reduzir o MVP implicitamente.

## Pendências e encaminhamento

| Pendência / PRD | Consequência atual | Destino / resolução necessária |
|---|---|---|
| L-08 — P01 — resolvida | Facebook escolhido explicitamente; acesso inicial por páginas sem login e sessão condicional. | E-PS5-DEC-01; reavaliar DOC-RECOMENDACAO-02 e atualizar o aceite sem apagar o relatório anterior. |
| L-01 — P01 — parcial | Busca, detalhe e continuação demonstrados no Facebook; estabilidade e condições do acesso pretendido ainda não comprovadas. | F02 prepara dependências/configuração privada; F04 especifica coletor, acesso, limites e tratamento de sessão expirada. |
| L-02 — P03/P05 | Geografia, precisão e entrega do MVP não comprovadas. | F03 especifica entrada/estado; investigação complementar/F04 valida dados/raio/destino; F07 distingue frete informado/estimado. |
| L-03 — P09 | Histórico, vínculo de anúncio/republicação e recuperação desconhecidos. | F04 define identidade/observações/janela; F09 define deduplicação, retomada e eventos de redução. |
| L-04 — P07 | Sem amostra ou estimativa de revenda confirmada. | F06 define equivalência, atualidade, amostra, discrepantes e confiança com evidência real. |
| L-05 — P02 | Capacidade do conjunto não medida, apesar de inventário de leitura. | F02 fixa versões e verifica carga conjunta, limites e persistência. |
| L-06 — P02/P09 | WAHA sem imagem/digest/engine localmente validados; sem sessão/envio. | F02 valida lifecycle e configuração; F09 precisa de conta, sessão, destinatário e autorização específica para envio real. |
| L-07 | Frequência, latência e custo total desconhecidos. | Medições autorizadas para F04/F09; orçamento e consumo em F02. |
| L-09 | Parte das fontes bloqueada, sem conclusão universal de indisponibilidade. | Revalidar documentos/acesso antes de compromisso com qualquer integração. |

As lacunas originais têm contexto, data e próximo passo no [índice](evidence-index.md#lacunas-rastreadas); os complementos registram a resolução da escolha e as provas práticas. Nenhum risco foi aceito em nome do usuário. Incompatibilidade com requisito obrigatório deve voltar à decisão de produto, preservando IDs e histórico do PRD.

## Limites da entrega

Documentos contêm apenas evidência sanitizada: sem credenciais, cookies, telefone, CEP privado, QR code ou material de sessão. Nenhum commit, push ou PR; nenhum scaffold integrado. [environment.md](environment.md) prepara a integração seletiva F02 preservando o harness.
