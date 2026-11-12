# Percurso integrado e detalhe após reinício

Laboratório sintético próprio criado por `first_eligibility_scenario(sample_ready=False)`, iniciado com `scripts/init.sh --disposable` e limpo por sua factory. Fonte e WAHA em loopback; nenhuma operação no grupo real. Driver local: `.runtime/f16_integrated_browser.py`.

A oferta inicialmente incerta e sem comparáveis suficientes recebeu enriquecimento automático. O worker normal confirmou uma mensagem. O ambiente foi parado/iniciado normalmente; os handlers retomaram sem outro primeiro POST. A leitura SQL antes/depois comparou a mesma identidade, referência, corpo, recibo, data e grupo. `result.json` registra os valores sintéticos e a contagem de um POST/uma mensagem.

O `playwright-cli`, sessão exclusiva `f16-integrated-restart`, abriu `/ofertas/<mesmo Listing.id>/` depois da retomada. Capturas desktop 1440 e mobile 360 foram examinadas: a mesma oferta mantém compra1000, venda1500 e lucro350; o bloco exibe confirmação histórica, horário e a ressalva de que servidor não comprova entrega ou leitura. Não há overflow horizontal. O espaço de imagem explica a ausência de mídia da fixture. Consultas do navegador não alteraram chamadas, POSTs ou mensagens do WAHA fake. A sessão Chromium foi fechada e o laboratório descartável limpo.

Evidências: `browser.log`, `result.json`, `detail-after-restart-desktop.png` e `detail-after-restart-mobile.png`. Complementa UI01/02/03 sem reivindicar produtor F15, Facebook autenticado ou outro envio real.
