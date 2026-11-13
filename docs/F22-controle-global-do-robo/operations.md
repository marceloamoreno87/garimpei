# Operação — ligar e desligar o robô

Estado: F22 `done`, conforme a [avaliação de 2026-11-13](eval-report-2026-11-13T18-33-50Z.md). O controle está em **Acompanhamento**; a decisão é salva no PostgreSQL e conserva revisão/identificação de comando para concorrência e repetição segura.

| Estado apresentado | Interpretação e próximo passo |
|---|---|
| Robô ligado | Novas unidades podem ser autorizadas se worker, dados e bloqueios individuais permitirem. Isso não comprova processamento ativo nem envio. |
| Robô desligando | A pausa foi confirmada; operações já autorizadas ainda podem concluir e registrar resultado. Aguarde a leitura atualizada. |
| Robô desligado | Nenhuma nova unidade de negócio é admitida pelo controle. Consulta de ofertas, configuração e histórico continuam disponíveis. |
| Encerramento indeterminado | Algumas operações precisam de conferência; não presume cancelamento ou liberação do navegador/GPU. |
| Estado indisponível | Não há confirmação confiável para autorizar novo trabalho; reabra o acompanhamento e confira a decisão salva. |

**Desligar robô** impede novas unidades de coleta, pesquisa, mídia, avaliação/inferência e envio; não mata processos ou cancela à força uma chamada externa. Uma mensagem já autorizada pode terminar, e resultado incerto conserva seu vínculo de reconciliação.

**Ligar robô** permite retomar apenas trabalho ainda aplicável. Acesso Facebook suspenso, IA pausada, alertas desativados, barreiras de recuperação e dados vencidos mantêm seus efeitos. Novas reduções/primeiros alertas continuam sujeitos à política vigente; F21 ainda possui prova real positiva bloqueada.

Recarregar a página, fechar a aba, editar a configuração ou reiniciar serviços não substitui a intenção global confirmada. Se outra aba já alterou a revisão, confira a decisão atual antes de tentar outra vez. Erro de leitura/gravação não é confirmação de alteração.

Para encerrar web/worker e dependências próprias, use `./scripts/stop.sh` com o mesmo ambiente privado. Para apenas pausar trabalho automático, use o controle na interface. A [operação F02](../F02-fundacao-tecnica-e-ambiente-local/operations.md) descreve lifecycle; a [operação F17](../F17-resiliencia-operacional-e-progresso-verificavel/operations.md) descreve recuperação/backup.
