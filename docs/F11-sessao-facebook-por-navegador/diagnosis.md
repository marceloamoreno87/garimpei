# Diagnóstico e decisão — sessão Facebook

Em 2026-11-11, o usuário relatou perda de acesso ao copiar cookies pelo F12 para o Garimpei. Foi escolhido explicitamente o fluxo **janela própria com login manual e coleta automática**. Nenhuma tentativa nova no Facebook nem leitura dos valores de cookies foi feita durante o diagnóstico.

## Evidência confirmada

- O adaptador anterior cria Chromium headless e um contexto novo a partir de um arquivo de cookies. Não é uma continuação do navegador pessoal onde o usuário autenticou.
- A importação extrai somente `cookies`, mesmo de JSON com outras origens, e grava `origins: []`. Um cabeçalho Cookie também não carrega os atributos completos nem o restante do estado do navegador. Isso limita a fidelidade da transferência; não prova o motivo da rejeição pelo Facebook.
- O estado local observado tinha revisão gerenciada salva pela UI, sem sessão configurada por variável de arquivo, nenhuma coleta inicial concluída e `access_suspended=true`. O último ciclo terminou com `session_expired`. As contagens de razões correspondem a unidades lógicas do ciclo, não a uma contagem de requisições reais: o adaptador evita novas navegações após falha de acesso.
- Defaults eram decididos antes de resolver a sessão gerenciada: timeout 5 s, retry base 15 s e intervalo 300 s, enquanto o fluxo autenticado por arquivo recebia 20/900/600 s. A regressão reproduziu essa diferença; a resolução foi movida para depois da escolha do tipo de sessão, preservando overrides explícitos.

## O que permanece hipótese

Não foi reproduzido um veredito remoto de detecção de robô, nem determinado o sinal que encerrou a sessão. Troca de contexto, estado incompleto, validade da sessão, política da plataforma e padrão da coleta podem contribuir. `session_expired` é o diagnóstico do adaptador diante da página/cookies observados, não a explicação interna do Facebook. Abrir janela visível ou reter perfil não comprova aceitação de automação.

## Decisão aplicada

Perfil privado exclusivo do Garimpei, com navegador visível e autenticação pelo usuário. O worker mantém a janela enquanto o usuário entra e confirma desafios; a interface exige **Já entrei, verificar acesso**. Depois de verificação autenticada no Marketplace, o perfil é fechado/gravado e liberado para coleta. Coletas reabrem esse perfil; um lock impede dois navegadores de usá-lo ao mesmo tempo. Desafios posteriores pausam a coleta. Reinício não autoriza retentar acesso suspenso. A janela do navegador pessoal não é acessada nem modificada.

Alternativa apresentada: coleta assistida durante navegação manual. Ela muda o requisito de monitoramento automático e não foi escolhida. O perfil novo não emprega o hook stealth nem os flags de ocultação existentes no caminho legado de cookies. Não foram adicionadas rotação de identidade ou soluções para contornar desafios.

## Fontes e limites

O Playwright documenta que a autenticação pode depender de cookies, localStorage e IndexedDB; carregar cookies não equivale a preservar todo o contexto. [Autenticação no Playwright](https://playwright.dev/python/docs/auth).

Contexto persistente mantém dados do navegador em diretório próprio e não admite duas instâncias com o mesmo diretório. O perfil padrão pessoal do Chrome não deve ser usado para essa automação. [BrowserType / contexto persistente](https://playwright.dev/python/docs/api/class-browsertype#browser-type-launch-persistent-context), [mudanças de segurança do Chrome](https://developer.chrome.com/blog/remote-debugging-port).

Validação local usa Chromium real, cookies/armazenamento sintéticos e origem loopback exclusiva de eval. É prova de persistência e coordenação da aplicação; login e aceitação reais exigem o usuário e permanecem pendentes.
