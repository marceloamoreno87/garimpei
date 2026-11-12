---
name: playwright-cli
description: Navegar e verificar interfaces do Garimpei pelo playwright-cli instalado, capturando snapshots e screenshots de jornadas críticas.
---

Use o executável `playwright-cli`; consulte `--help` e a ajuda do subcomando para opções desta versão. Confirme a aplicação com `./scripts/init.sh` antes da jornada. Cada execução usa sessão própria para não interferir em outra feature.

A configuração do projeto em `.playwright/cli.config.json` usa Chromium headless isolado. Instale o navegador com `playwright-cli install-browser chromium` quando o cache não existir. Fora da raiz, informe `--config=<raiz>/.playwright/cli.config.json` no comando `open`.

Exemplo de navegação (substitua a URL e referências pelos valores observados):

```bash
playwright-cli -s=garimpei-F01 open http://localhost:3000
playwright-cli -s=garimpei-F01 snapshot
playwright-cli -s=garimpei-F01 click e12
playwright-cli -s=garimpei-F01 screenshot
playwright-cli -s=garimpei-F01 close
```

As referências `e12` etc. vêm do snapshot atual. Refaça o snapshot depois de navegação ou mudança de DOM. Use `fill`, `press`, `upload`, `resize`, `eval`, `console` e `network` conforme a ajuda do CLI e a necessidade da jornada. Examine screenshots em verificações visuais e registre esperado/observado.

Guarde evidências junto da feature ou em `.playwright-cli/`, conforme o relatório, e encerre a sessão ao terminar. Não gere um projeto paralelo de testes Playwright nem pastas `e2e/` para substituir este fluxo. Credenciais e tokens ficam fora de snapshots e relatórios compartilhados.
