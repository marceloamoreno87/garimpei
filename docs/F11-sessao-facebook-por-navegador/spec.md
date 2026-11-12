# F11 — Sessão Facebook por navegador

Decisão do usuário: janela própria com login manual e coleta automática, em substituição à cópia habitual de cookies. Perfil privado dedicado, distinto do navegador pessoal; login e desafios resolvidos pelo usuário na janela. O perfil mantém cookies e armazenamento local entre execuções. Isso não promete impedir detecção nem superar um bloqueio da plataforma.

O menu Integrações permite abrir a janela, acompanhar abertura/espera, confirmar o login e verificar acesso ao Marketplace. A confirmação exige sessão autenticada, não apenas fechar a janela. A coleta fica suspensa durante login, falha, interrupção e desafios. Um único dono utiliza o perfil por vez; parada normal conserva o perfil e reinício não libera um acesso suspenso. Ofertas, marcos iniciais e recibos não são apagados. Cookies importados continuam como opção avançada de compatibilidade, com os mesmos parâmetros padrão do acesso real.

O worker existente mantém a janela de login por até 15 minutos. A interface persiste comandos e status, sem senha, cookies ou tokens na resposta. Verificação bem-sucedida fecha e grava o perfil antes de retomar a coleta. As coletas reutilizam o mesmo diretório e usam navegador visível. O processo continua sendo automatizado; desafios exigem ação humana e nenhuma tentativa de bypass integra esta mudança.

Dependências F04/F10 implementadas, com pendências reais anteriores preservadas. A nova instrução autoriza a extensão antes do aceite externo F09/F10. Ambiente WSLg disponível. Login real exige a participação do usuário; provas locais usam apenas origem HTTP loopback isolada de avaliação.
