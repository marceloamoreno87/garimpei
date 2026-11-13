# Operação — acompanhamento e cópias dos dados

Estado: F17 `done`, conforme a [avaliação registrada](eval-report-2026-11-13T03-39-54Z.md) e o [progresso](../prd_progress.json). Este guia descreve a implementação atual; checkpoints de correção anteriores continuam históricos.

## Acompanhamento

Abra **Acompanhamento** para consultar coleta, etapas, percurso e pesquisas. Os números representam recortes distintos: não devem ser somados. Cada etapa informa estado, motivo, último avanço e próxima tentativa quando disponíveis. Use a retomada apenas quando a interface a oferecer; revisão obsoleta, acesso suspenso e barreira de restauração precisam de recuperação específica.

Atualização falha conserva a última leitura. No carregamento inicial do percurso, use **Tentar carregar percurso**. Fechar a aba não para web/worker. O controle global **Desligar robô** pausa novas unidades de negócio e conserva consultas, sem substituir a parada dos processos.

## Cópias e exportação

Em **Cópias dos dados**, confira última cópia, próxima operação e histórico. A política mantém as sete últimas cópias concluídas e prevê uma cópia a cada 24 horas de operação. Exportar uma cópia concluída cria um artefato para baixar e guardar fora do mesmo disco. Integridade verificada não significa restauração testada.

A configuração privada `GARIMPEI_BACKUP_DIR` deve apontar para um diretório próprio fora do checkout. Falta de espaço, mídia requerida ausente ou arquivo inválido impedem uma cópia completa. A reserva mínima de 1 GiB é uma proteção; selecione armazenamento apropriado em vez de reduzir a proteção para fazer um teste passar.

Com o arquivo privado de ambiente selecionado e a aplicação preparada, de `apps/backend/`:

```bash
uv run --frozen --no-sync python manage.py operational_backup list
uv run --frozen --no-sync python manage.py operational_backup create
uv run --frozen --no-sync python manage.py operational_backup verify --id UUID_DA_COPIA
uv run --frozen --no-sync python manage.py operational_backup export --id UUID_DA_COPIA
```

Os valores `UUID_DA_COPIA` são substituídos pela identificação real do catálogo; não são caminhos fornecidos por uma requisição HTTP. A CLI usa configuração central e retorna erro quando não conclui a operação.

## Recuperação

Restauração é operação explícita em destino `eval` isolado, próprio, descartável e vazio, usando `operational_backup restore --archive CAMINHO_PRIVADO --isolated`. A restauração mantém o despacho bloqueado até reconciliar o intervalo posterior à cópia. Não use um banco com dados reais como destino de ensaio.

Sessões Facebook/WhatsApp, segredos e pesos do modelo exigem recuperação separada. Partes confirmadas, mídia protegida, histórico e recibos seguem o formato validado; permissões e gerações de trabalho em curso são reconstruídas segundo o contrato. A retomada do robô não remove a barreira de recuperação nem transforma um envio incerto em autorização de novo POST.

Procedimentos, limites e cenários detalhados estão no [contrato](contract.md); a [arquitetura implementada](../architecture/implementation.md) localiza os adaptadores e comandos atuais.
