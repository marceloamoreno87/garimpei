# Revisão da entrega F07

Revisão nesta sessão, sem delegação. Conferidos spec, plano, contrato e AC01–04 do PRD contra os doze arquivos alterados do backend; hashes em reviewed-inputs.json. Nenhuma exclusão, alteração de dependências do produto ou mudança de requisito.

- Domínio puro usa Decimal, HALF_UP na taxa e preserva zeros. Retirada ignora frete e precede envio. Componentes indisponíveis preservam os conhecidos; não há filtro mínimo de lucro.
- Caso de uso recebe porta e relógio por construtor, obtém um único instante e chama a mesma política para anúncio/evento.
- Adaptador lê configuração ativa, observação e avaliação em REPEATABLE READ; herda somente transação externa já consistente. Conflito de leitura vira erro repetível e sanitizado. Não há rede na consulta.
- Evento carrega a própria observação; contexto é revalidado pelo escopo F04 e configuração atual. Produto e validade da revenda são conferidos novamente pela política, sem recorrer a preço de novo.
- DTO conserva revisões e identidade da avaliação histórica para F08 e a composição para captura F09. Custos excluídos são explícitos.
- Integração adicionada somente ao main, ao diagnóstico JSON e às fixtures/consumidores de qualidade necessários. Nenhum arquivo anterior removido.
- Prontidão/lifecycle são exercitados pelos testes PostgreSQL descartáveis, com limpeza em finally. Manifesto/health e dados observados aparecem em service.txt após a execução.

Limite conhecido documentado: chamar dentro de READ COMMITTED retorna ProfitReadFailed; consumidores podem consultar fora da transação ou abrir REPEATABLE READ/SERIALIZABLE. Não é prometida persistência do cálculo por F07: cabe a F09 conservá-lo junto à decisão.
