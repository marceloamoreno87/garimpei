# F11 — Conectar o Facebook

Com o sistema rodando, abra **Integrações → Facebook Marketplace**. Nesta instância: http://localhost:18351/integracoes/.

1. Clique em **Abrir navegador do Facebook**. Aguarde a janela própria do Garimpei neste computador.
2. Faça login nessa janela. Resolva ali qualquer confirmação solicitada pelo Facebook e verifique se consegue acessar o Marketplace.
3. Volte ao Garimpei e clique em **Já entrei, verificar acesso**. Aguarde **Sessão verificada**. A janela de login será fechada para gravar o perfil e liberar a coleta; o coletor reabrirá o mesmo perfil em janela visível.

Não feche a janela antes de confirmar no Garimpei. Durante o login, a coleta fica pausada. A janela tem prazo de 15 minutos. Se for fechada ou houver interrupção, clique para abrir novamente. Se a sessão do Facebook exigir confirmação mais tarde, a coleta pausa e o Garimpei oferece reconexão; reiniciar o sistema não libera esse bloqueio.

O diretório `facebook-browser` fica dentro do diretório privado de integrações da instância, externo ao checkout e com modo 0700. Cookies e armazenamento são mantidos pelo Chromium; não é necessário exportá-los pelo F12. O perfil é próprio do Garimpei e não altera o perfil pessoal. Uma parada normal preserva os dados. A sessão gráfica WSLg precisa estar disponível para abrir a janela.

**Opção avançada: importar cookies** conserva a compatibilidade anterior. Essa opção importa cookies e não o perfil completo. Salvar cookies troca de volta para o modo legado e interrompe o fluxo de login pendente. Nenhuma senha ou token deve ser enviado pela conversa ou incluído em evidências.

O processo de coleta continua automatizado. Persistência do perfil não garante que a plataforma aceite a atividade. A prova real consiste em autenticar na janela, confirmar, observar uma coleta e uma reabertura preservando sessão. Testes locais comprovam persistência e pausa/retomada, sem atestar esse resultado externo.
