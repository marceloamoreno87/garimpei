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

O destino precisa do marcador `.runtime/<ambiente>/docker-disposable` da instância descartável e das mesmas superfícies de dados que os arquivos da cópia exigem. Diretórios de destino precisam estar vazios. Esse marcador não é autorização para apagar recursos. O helper não apaga bancos, volumes ou perfis.

```bash
./scripts/docker-adoption.sh restore-check garimpei-eval_destino /caminho/privado/fora-dos-dados/copia
```

O comando verifica checksums antes de acessar Docker, proprietário e estado de cada recurso antes da primeira escrita, banco vazio, saída do `pg_restore`, admissão restaurada ainda pausada e igualdade de contagens de todas as tabelas. Copia arquivos preservando IDs de proprietário. Inferência vai para o ambiente de destino; PIDs, locks e manifests transitórios da origem não são adotados. Não abrir simultaneamente o mesmo perfil. Uma falha depois do início da restauração deixa um destino parcial e parado; usar outro destino vazio após investigar, sem insistir sobre dados existentes.

Antes de adotar, conferir também IDs/revisões/hashes, conteúdo e permissões das sessões/perfis, mídia, tokenizer/pesos e recibos, aplicar migrations sob lock e demonstrar prontidão/heartbeats. Comparar a última intenção/tentativa/recibo de envio com o inventário. O helper preserva uma operação `unknown`, mas não decide se houve transmissão. Recuperação de GPU incerta permanece pelo wrapper próprio F19/F23.

## Rollback

Conservar a cópia fria e o backup F17 verificado, junto da versão/imagens anteriores. Restaurar em outro destino próprio vazio com a versão compatível; não sobrescrever a instalação atual. Repetir verificações de banco, arquivos e barreira antes da troca. Se houve atividade após o backup, preservar também o registro mais recente de intenções/tentativas/recibos e reconciliar a janela antes de liberar qualquer envio. Uma cópia antiga não demonstra ausência de transmissão posterior.

A pausa restaurada é obrigatória. Não ligar robô, alertas ou IA automaticamente após o rollback. A retomada exige reconciliação F17/F16 e revalidação de revisões/prazos pelas políticas atuais. Arquivo `restore-<ambiente>` indica que o helper terminou suas verificações; não é aprovação da adoção, da qualidade da IA ou de uma transmissão.

## Limite da evidência automatizada

`evidence/migration-mechanics-*.json` registra um ensaio isolado com PostgreSQL real e superfícies de arquivos sintéticas em contêineres parados. Verifica dump/restauração, contagens, bytes de mídia/perfil/sessões/pesos/tokenizer, corpo congelado, operação incerta e pausa, além da recusa de restauração sobre banco preenchido. Os contêineres de arquivos desse ensaio usam a imagem PostgreSQL somente como armazenamento; não são processos reais de web, WAHA ou Ollama. Isso não comprova adoção de uma instalação anterior, backup F17 completo nem o item E2E-PERSISTENCIA-01 inteiro. Esses limites devem permanecer na avaliação canônica.
