# Verificação visual — prova real F21, worktree ef90

Sessões próprias `playwright-cli`, Chromium isolado, instância `eval_f21_proof2_ef90`, porta24636. Scripts canônicos de inicialização e publicação da projeção F08 executados. Interface e estilos não foram alterados nesta correção.

## Observações verificadas

| Superfície | Observado | Evidência |
|---|---|---|
| Detalhe real1004776551984738 | Fotos locais, título original, equivalência iPhone13/128GB, compra1400, venda estimada1600, taxa10%/160, lucro40. A existência de lucro positivo não autorizou alerta com condição insuficiente/defeito. | `real-target-desktop-final.png`, `real-target-finance-390.png` |
| Mídia | Cinco imagens do primeiro alvo carregadas (`complete` e `naturalWidth>0`), por rotas locais da oferta. | Console de avaliação e screenshot desktop |
| Largura390 | `innerWidth=390`, `documentElement.scrollWidth=390`. Valores e diagnóstico continuam legíveis; não houve rolagem horizontal. | `real-target-390.png`, `real-target-finance-390.png` |
| Análise parcial1902857791096295 | Seis imagens locais carregadas. A qualificação informa que aguarda análise, conserva nome normalizado,10comparáveis/mediana de preços pedidos e limite real do primeiro alerta13/11/2026 23:17:20UTC. Não apresenta recibo ou ouro. | `partial-condition-390.png`, `partial-condition-snapshot.txt` |
| Revisões | Mudança de configuração/observação no lab conservou a leitura publicada e mostrou “Evidências alteradas; aguardando nova qualificação”. A leitura anterior não se tornou qualificação atual. | `real-target-blocked-390.png` |
| Navegação móvel | Menu aberto inspecionado por snapshot/screenshot, `aria-expanded=true` e largura390sem overflow. Tab para um link e Escape fecham a navegação, devolvendo foco ao botão (`aria-expanded=false`). | `menu-open-390.png`, `menu-open-snapshot.txt` |

Os avisos de Facebook desconectado e robô desligado correspondem ao ambiente de replay: o perfil real não foi copiado para a instância de avaliação. Eles não comprovam falha da coleta original, que ocorreu em perfil dedicado separado. Os GETs desta verificação não realizaram envios.

## Acabamento, conforme frontend-ui-design

| Dimensão | Nota | Evidência concreta |
|---|---:|---|
| Design, peso2 | 7 | Paleta Mineral consistente, separação entre imagens/referências/diagnóstico e identificação clara dos estados. Os avisos globais consomem uma parte relevante da primeira dobra. |
| Originalidade, peso2 | 6 | Vocabulário próprio de garimpo e composição orientada a produto/comparação; layout e navegação seguem padrões convencionais do sistema existente. |
| Acabamento, peso1 | 8 | Valores, nomes e IDs quebram linha em390px; imagens carregam, superfícies e espaçamentos são consistentes. |
| Funcionalidade, peso1 | 8 | Rótulos distinguem estimativa, condição e autorização; referências e seções podem ser alcançadas sem perder a oferta. |

Média ponderada7,0/10; nenhuma dimensão abaixo do limiar3. Avaliação visual por IA, sem teste com pessoas ou leitor de tela. Como melhoria localizada, Escape com foco ainda no próprio botão de menu não o fecha; Escape após entrar na navegação fecha e restaura o foco. Esse comportamento já existe no código de navegação e não altera a autorização F21.

## Ocorrências do procedimento

A primeira consulta de detalhe retornou404 porque o driver ainda não havia publicado a projeção de exploração; a publicação pelo caso de uso F08 resolveu o acesso. O encerramento normal do driver interrompeu polling do navegador, que conservou a leitura com mensagem recuperável. Depois da reinicialização própria, consultas e mídias voltaram a responder. As capturas finais distinguem esses estados; não se tratou o primeiro404 ou a conexão encerrada como sucesso.

Estas observações cobrem os casos reais negativos e parciais. Não substituem um caso real qualificado, a avaliação controlada anterior da BASE ou a regressão completa coordenada.
