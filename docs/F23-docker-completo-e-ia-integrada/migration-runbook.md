# Migração e rollback do runtime F23

O helper `scripts/docker-adoption.sh` fornece uma cópia fria privada e restauração em destino Docker descartável vazio. Não inicia web, worker, navegador, WAHA ou Ollama e não autoriza retomar envios. Complementa o backup de negócio F17: esse backup exclui autenticação e jobs técnicos, enquanto a cópia fria conserva o banco completo, arquivos privados, inferência, sessão WAHA e pesos quando os respectivos contêineres existem.

A origem e o destino precisam ter labels `com.garimpei.checkout` iguais ao checkout que executa o helper e `com.garimpei.environment` compatível com o projeto Compose. Volumes nomeados também precisam das duas labels. O banco precisa se chamar `garimpei_<ambiente>`. Um arquivo ausente durante a cópia impede sua conclusão; ausência de contêiner opcional fica explícita no inventário privado e não comprova conservação daquele serviço.

## Preparar a origem

1. Identificar versão de código/imagens e recursos existentes. Registrar contagens, revisões, filas, intenções e recibos; preservar o arquivo privado de configuração fora do Git.
2. Confirmar pausa global pela interface F22. Esperar unidades admitidas drenarem; operação de término incerto permanece registrada e exige reconciliação própria. Não concluir uma unidade por timeout presumido.
3. Criar e verificar o backup de negócio F17 pelo comando `operational_backup` da versão de origem. Fazer sua restauração em uma instalação eval descartável independente e conferir a barreira F17 antes da adoção. O helper de cópia fria não substitui essa prova nem registra um backup F17 como restaurado.
4. Parar somente web, worker, login pontual, WAHA e Ollama próprios, deixando PostgreSQL ativo para o dump consistente. Conferir que nenhum navegador mantém o perfil aberto. O helper recusa contêiner não PostgreSQL em execução e admissão ainda ligada ou unidade ativa.
5. O worker deve ter um diretório de inferência, mesmo vazio, em `/state/<ambiente>/inference`. Arquivos e tokenizer serão remapeados para o diretório do ambiente de destino. Banco, arquivos privados e sessões permanecem congelados durante a cópia.

```bash
./scripts/docker-adoption.sh snapshot garimpei-eval_origem /caminho/privado/fora-dos-dados/copia
```

O diretório de saída precisa ser novo e externo à origem privada. Recebe modo 0700, dump completo, arquivos tar privados, inventário, contagens de todas as tabelas de aplicação e checksums SHA-256. `READY` aparece somente depois da cópia completa; sua ausência ou checksum divergente impede restauração. Não publicar o diretório: contém sessões, configurações e dados privados. O inventário registra IDs de imagens; não inclui conteúdo de variáveis de ambiente.

## Ensaiar a restauração

Preparar um projeto eval novo e recursos próprios com banco vazio, PostgreSQL ativo e contêineres de dados criados e parados. Não executar migrations no destino antes da restauração do dump completo. Usar as mesmas imagens/pins da origem para verificar a cópia antes de migrar o schema; eventual atualização de código é um passo posterior explícito.

O destino precisa do marcador `.runtime/<ambiente>/docker-disposable` da instância descartável e das mesmas superfícies de dados que os arquivos da cópia exigem. Diretórios de destino precisam estar vazios de dados. `/private/.garimpei-owner` deve existir, ser arquivo regular e corresponder ao checkout e ambiente do destino, conforme preparado pelo controlador. A cópia exclui os três metadados de propriedade da origem: `.garimpei-owner`, `media/.garimpei-media-owner` e `backups/.garimpei-backup-owner`. Preserva o marcador do controlador de destino e prepara os marcadores dos stores com o ID do destino, sem newline e com modo 0600, usando o proprietário do diretório privado antes de importar seu conteúdo. Marcadores preexistentes só são aceitos se regulares e correspondentes ao destino. Cópias antigas que incluam esses metadados são recusadas antes de restaurar o banco. O host precisa de GNU tar para excluir esse metadado sem extrair sessões em diretório temporário. Esse marcador não é autorização para apagar recursos. O helper não apaga bancos, volumes ou perfis.

```bash
./scripts/docker-adoption.sh restore-check garimpei-eval_destino /caminho/privado/fora-dos-dados/copia
```

O comando verifica checksums antes de acessar Docker, proprietário e estado de cada recurso antes da primeira escrita, banco vazio, saída do `pg_restore`, admissão restaurada ainda pausada e igualdade de contagens de todas as tabelas. Copia arquivos preservando IDs de proprietário. Inferência vai para o ambiente de destino; PIDs, locks e manifests transitórios da origem não são adotados. Não abrir simultaneamente o mesmo perfil. Uma falha depois do início da restauração deixa um destino parcial e parado; usar outro destino vazio após investigar, sem insistir sobre dados existentes.

A cópia fria não transporta `recovery-barrier.json` nem cria uma barreira de recuperação local automaticamente. Antes de iniciar qualquer worker no destino ou no rollback, estabelecer uma barreira F17 local bloqueada, associada ao backup verificado e ao ID da instalação de destino, e comprovar `build_recovery_guard()() == True`. Manter também F22 desligado. O [ensaio reproduzível](evidence/predecessor-final.md) registra criação do registro `RecoveryBarrier`, arquivo local e chamada ao guard real antes dos probes e reinícios; não há liberação ou reconciliação presumida.

Antes de adotar, conferir também IDs/revisões/hashes, conteúdo e permissões das sessões/perfis, mídia, tokenizer/pesos e recibos, aplicar migrations sob lock e demonstrar prontidão/heartbeats. Comparar a última intenção/tentativa/recibo de envio com o inventário. O helper preserva uma operação `unknown`, mas não decide se houve transmissão. Recuperação de GPU incerta permanece pelo wrapper próprio F19/F23.

## Rollback

Conservar a cópia fria e o backup F17 verificado, junto da versão/imagens anteriores. Restaurar em outro destino próprio vazio com a versão compatível; não sobrescrever a instalação atual. Repetir verificações de banco, arquivos e barreira antes da troca. Se houve atividade após o backup, preservar também o registro mais recente de intenções/tentativas/recibos e reconciliar a janela antes de liberar qualquer envio. Uma cópia antiga não demonstra ausência de transmissão posterior.

A pausa restaurada é obrigatória. Não ligar robô, alertas ou IA automaticamente após o rollback. A retomada exige reconciliação F17/F16 e revalidação de revisões/prazos pelas políticas atuais. Arquivo `restore-<ambiente>` indica que o helper terminou suas verificações; não é aprovação da adoção, da qualidade da IA ou de uma transmissão.

## Evidência de adoção e rollback controlados

O ensaio `evidence/predecessor-proof-20261114003250.json` executou a versão anterior `15079aa`/schema0027, gerou backup F17 e o restaurou em uma segunda base antes da adoção. Depois verificou cópia fria, igualdade de todas as linhas anteriores às migrations, aplicação de 0030/0031, reinício real de PostgreSQL com dados persistentes e do worker, além de rollback em uma quarta base vazia com código anterior. Leitura real do original/miniatura e resposta HTTP 200 confirmaram acesso à mídia no destino e no rollback. O ArchiveGateway preparou seu diretório e criou/leu um novo backup F17 em ambos. Recibos, corpos, revisões, configurações e o job técnico original permaneceram preservados; a sondagem de transmissão sob barreira não fez novo POST. A comparação após reinício permite somente o timer operacional `media_refresh_after`, com os três diffs de campo registrados explicitamente.

O banco e os processos de worker são reais; perfis/sessões/pesos e resultados anteriores usados como dados de persistência são sintéticos identificados. Isso comprova o ensaio previsto no contrato sem alegar adoção da instalação pessoal, sessão pareada real ou qualidade do modelo. Dumps, arquivos privados e credenciais geradas permanecem fora do Git. As rodadas anteriores com erros de fixture/ambiente foram preservadas; o relatório final identifica a rodada válida.

## Limite do ensaio mecânico inicial

`evidence/migration-mechanics-*.json` registra um ensaio isolado com PostgreSQL real e superfícies de arquivos sintéticas em contêineres parados. Verifica dump/restauração, contagens, bytes de mídia/perfil/sessões/pesos/tokenizer, corpo congelado, operação incerta e pausa, além da recusa de restauração sobre banco preenchido. Os contêineres de arquivos desse ensaio usam a imagem PostgreSQL somente como armazenamento; não são processos reais de web, WAHA ou Ollama. Isso não comprova adoção de uma instalação anterior, backup F17 completo nem o item E2E-PERSISTENCIA-01 inteiro. Esses limites devem permanecer na avaliação canônica.
