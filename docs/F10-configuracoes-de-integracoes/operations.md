# F10 — Operação das integrações

Atualização F11: o fluxo principal Facebook agora é [login pela janela própria com perfil persistente](../F11-sessao-facebook-por-navegador/operations.md). A importação de cookies abaixo permanece na opção avançada. WhatsApp continua conforme este guia.

Com o ambiente iniciado por `./scripts/init.sh`, abra **Integrações** no menu do Garimpei. A instância de desenvolvimento desta execução está em http://localhost:18351/integracoes/.

## Facebook

1. Entre no Facebook no seu navegador e conclua qualquer confirmação de acesso solicitada.
2. Em Integrações, abra **Como obter os cookies**. Cole o valor do cabeçalho `Cookie` de uma requisição para `facebook.com`, um JSON exportado de cookies ou um estado de sessão Playwright. São necessários `c_user` e `xs`.
3. Clique em **Salvar cookies**. O campo fica vazio após salvar. “Aguardando verificação” significa que o arquivo foi salvo; “Sessão verificada” exige uma coleta concluída depois dessa revisão. Complete também a configuração de monitoramento para iniciar a coleta.

Quando a validade conhecida terminar ou a coleta detectar autenticação exigida, a aplicação mostra um aviso persistente e **Renovar cookies**. Se houver checkpoint, conclua a verificação no Facebook antes de copiar novos cookies. A renovação retoma o coletor sem reiniciar o sistema, mantém as ofertas e conserva o marco da carga inicial. Sessões sem data de validade só podem ter a expiração detectada ao consultar a fonte. O aviso é exibido no Garimpei, não enviado por WhatsApp.

Os cookies ficam em arquivos privados por revisão, fora do checkout. O padrão é `~/.local/share/garimpei/integrations/<environment_id>`; o operador pode configurar `GARIMPEI_INTEGRATION_PRIVATE_DIR` fora do repositório. Um diretório existente precisa ser privado. Não coloque esses arquivos em logs, relatórios ou controle de versão. Revisões anteriores são preservadas para evitar conflito com navegadores ainda em curso; contêm credenciais e devem permanecer privadas.

## WhatsApp

1. Clique em **Conectar WhatsApp**. No celular, abra WhatsApp → Aparelhos conectados → Conectar aparelho e escaneie o QR apresentado.
2. Aguarde **WhatsApp conectado**. Escolha o grupo na lista dos grupos dessa conta. Se ele não aparecer, entre no grupo pelo WhatsApp e clique em **Atualizar grupos**.
3. Marque **Ativar alertas neste grupo** e clique em **Salvar grupo e alertas**. A seleção só é aceita se o grupo ainda pertencer à conta conectada.

Conectar e salvar não enviam mensagem de teste. Os próximos eventos elegíveis seguem as regras F09; carga inicial, condição e estimativa financeira continuam determinando o envio. **Desativar alertas** mantém o grupo, a sessão e os recibos. A troca de grupo vale para novas intenções; intenções anteriores conservam seu destino para reconciliação, evitando reenvio ou redirecionamento incerto.

Se a conta mudar, escolha e salve novamente o grupo. Se o serviço ou a sessão estiverem indisponíveis, use a ação de recuperação exibida. A chave WAHA permanece no backend; a rota do QR não inclui a chave na URL. Configuração e sessão persistem na parada/inicialização normais; não use `stop.sh --clean` para preservar os dados de desenvolvimento.

## Compatibilidade e validação

Antes da primeira configuração pela interface, as variáveis privadas F04/F09 continuam válidas. Cookies e destino salvos na UI passam a ter precedência. O destino também admite IDs canônicos de grupo `@g.us`, além dos destinos diretos legados `@c.us`.

As provas automatizadas usam instâncias descartáveis e HTTP programável, incluindo o worker e o fluxo financeiro completos. A leitura de um QR sintético não comprova pareamento real. Cookies reais, pareamento e entrega na conta do usuário permanecem para validação na aplicação; não compartilhe credenciais na conversa.

## Atualização automática de conexão

Ao mudar entre conectado e não conectado, o Garimpei recarrega a página para atualizar grupos/ações, inclusive se a URL atual já termina em `#whatsapp`. Enquanto o estado permanece igual, o polling não descarta a seleção de grupo ainda não salva.
