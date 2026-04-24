# Projeto API Gerax - Regras de Arquitetura

Este projeto deve seguir uma arquitetura FastAPI em camadas.

## Camadas obrigatórias

- `app/api/v1/endpoints`: somente rotas HTTP.
- `app/services`: regras de negócio.
- `app/repositories`: acesso ao banco.
- `app/models`: modelos SQLAlchemy.
- `app/schemas`: modelos Pydantic.
- `app/integrations/nextrouter`: único local autorizado a chamar a API NextRouter.
- `app/utils`: funções utilitárias puras.
- `app/core`: configuração, segurança, logging e erros.
- `app/db`: conexão e base do banco.
- `app/workers`: jobs e coletores.

## Regras obrigatórias

1. Rotas FastAPI não podem chamar `requests`, `httpx` ou API NextRouter diretamente.
2. Repositories não podem chamar API externa.
3. Services podem chamar integrations e repositories.
4. Tokens, API keys e senhas nunca podem aparecer em logs.
5. Dinheiro deve usar `Decimal`, nunca `float`.
6. O endpoint `/api/getbalance/get/{username}?password=...` é proibido.
7. Operações financeiras não podem ter retry automático cego.
8. Toda chamada externa deve passar por `app/integrations/nextrouter/client.py`.
9. A estrutura de arquivos deve ser validada antes de implementar novas features.