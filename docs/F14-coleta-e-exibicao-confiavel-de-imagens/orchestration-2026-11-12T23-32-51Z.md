# Orchestration Journal — F14 Coleta e exibição confiável de imagens

**Run:** `2026-11-12T23-32-51Z`  
**Branch:** `wave/resume-f14`  
**Retry budget:** 3  
**Status:** `aborted`

## Entrada e evidência

Inspeção complementar dos três anúncios fornecidos para tentar abrir o visualizador de fotos. Lock do perfil dedicado confirmado livre e adquirido pela aplicação; navegador fechado e lock liberado ao término. Nenhum banco principal ou serviço foi iniciado, e não houve contato ou compra.

Para cada anúncio, foi selecionada uma imagem visível correlacionada a um PhotoID do próprio anúncio. Verificou-se o alvo no centro e excluiram-se ancestrais com rótulos de contato ou compra antes de despachar um clique DOM em cada imagem ou controle de foto identificado. O diagnóstico registrou três cliques despachados e zero diálogos após espera; não prova que um visualizador foi aberto. A observação dos documentos iniciais e respostas GraphQL durante a tentativa não detectou duas dimensões para nenhuma das seis fotos correlacionadas. Os hashes e dimensões estão em `evidence/source-viewer-2026-11-12T23-32-51Z.json`, sem URLs ou credenciais.

Esta inspeção não esgota todas as formas de abrir o visualizador ou acessar variantes; não demonstra que a fonte nunca as oferece. Não foram feitos download, comparação de arquivos, percurso de apresentação ou avaliação integral. Gates não foram repetidos. A avaliação anterior está em `eval-report-2026-11-12T20-12-37Z.md`.

## Veredito

**Status:** `aborted`  
**Ciclos de correção:** 0  
**Relatório novo:** nenhum; pré-requisito de amostra com variantes permanece não demonstrado.  
**Pendente:** `E2E-FONTE-01`; F14 permanece `implemented`.
