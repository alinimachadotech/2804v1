# api-gerax / Gerax Hub

API FastAPI read-only para consultar multiplos routers NextRouter C4 SoftSwitch.

O projeto atua como uma camada segura de consulta, normalizacao, cache, historico e observabilidade para o Gerax Hub, entregando dados para frontend Vue, Prometheus, Grafana e rotinas internas de operacao.

> Projeto privado/proprietario. Nao publique credenciais, tokens, IPs sensiveis ou arquivos `.env`.

## Escopo read-only

O api-gerax nao altera dados no NextRouter.

Fora do escopo:

```text
POST /api/statusCustomer
POST /api/manageCredit
DELETE /api/onlineCalls
```

Nao criar endpoints internos para:

```text
ativar cliente
desativar cliente
creditar saldo
debitar saldo
definir saldo
encerrar chamada
```

Todas as chamadas do `NextRouterClient` para o NextRouter devem usar `GET`. Tokens e keys ficam somente no backend e devem ser mascarados em logs.

## Stack

- FastAPI
- Pydantic
- SQLAlchemy
- MariaDB
- Redis cache
- Prometheus metrics
- Grafana
- pytest

## Configuracao local

Crie o ambiente virtual:

```powershell
python -m venv .venv
```

Instale dependencias:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

Copie o exemplo de ambiente:

```powershell
Copy-Item .env.example .env
```

Edite somente o `.env` local. Nunca versionar `.env`.

## Servicos de apoio

Subir MariaDB, Adminer, Prometheus e Grafana:

```powershell
docker compose --env-file .\.env -f .\docker\docker-compose.monitoring.yml up -d
```

Servicos locais esperados:

```text
MariaDB     localhost:3317
Adminer     http://localhost:8187
Prometheus  http://localhost:9090
Grafana     http://localhost:3180
```

## Rodar API

```powershell
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload
```

URLs:

```text
API          http://127.0.0.1:8000
Swagger      http://127.0.0.1:8000/docs
Metrics      http://127.0.0.1:8000/metrics
```

## Endpoints principais

Saude:

```text
GET /
GET /ping
GET /health
GET /api/v1/health
GET /api/v1/ready
GET /metrics
```

Clientes:

```text
GET /api/v1/customers/{customer_id}
GET /api/v1/customers/{customer_id}/balance
GET /api/v1/customers/{customer_id}/credit-history
```

NOC:

```text
GET /api/v1/noc/online/calls
GET /api/v1/noc/online/aggregate
GET /api/v1/noc/online/routes
GET /api/v1/noc/online/clients
GET /api/v1/noc/online/servers
```

Relatorios:

```text
GET /api/v1/reports/cdr
GET /api/v1/reports/cdr-disconnections
GET /api/v1/reports/sip-codes
GET /api/v1/reports/profit/customers
GET /api/v1/reports/profit/gateways
```

Exemplos de desenvolvimento e validacao manual devem consultar apenas 1 dia,
preferencialmente o dia anterior para relatorios fechados. Isso e uma regra
operacional para testes seguros, nao um bloqueio funcional da API:

```text
GET /api/v1/reports/cdr?router_name=Router%20Test&date_ini=2026-05-12&date_end=2026-05-12&start=0&limit=100
GET /api/v1/reports/profit/customers?router_name=Router%20Test&date_ini=2026-05-12&date_end=2026-05-12&customers[]=25&customers[]=39&gateways[]=1&gateways[]=5&start=0&limit=100
```

Contacts:

```text
GET /api/v1/contacts
```

## Consultas NextRouter permitidas

O `NextRouterClient` deve manter apenas:

```text
get_customer_balance
get_customer
get_credit_history
get_online_calls
get_online_calls_aggregate
get_cdr
get_cdr_disconnection
get_cdr_sipcodes
get_profit_customers
get_profit_gateways
get_contacts
```

## Seguranca

Regras obrigatorias:

- Nunca versionar `.env`.
- Nunca publicar tokens, keys, senhas ou IPs sensiveis reais.
- Nunca colocar token/key do NextRouter no frontend.
- Nunca colocar token/key do NextRouter no Grafana.
- Nunca logar URL completa contendo credenciais.
- Usar `.env.example` apenas com valores ficticios.
- Mascarar segredos em logs.
- Usar `Decimal` para dinheiro.
- Usar paginacao `start` e `limit`.
- Tratar erros 400, 403, 404, 413, 422, 429 e 5xx da integracao NextRouter.
- Nao usar `verify=False` fixo em producao.

## Testes

Rodar todos os testes:

```powershell
.\.venv\Scripts\python.exe -m pytest
```

Verificar arquivos sensiveis versionados:

```powershell
git ls-files | Select-String -Pattern "\.env|\.venv|backups|aplicar_"
```

A unica saida aceitavel relacionada a `.env` e:

```text
.env.example
```

## Banco de dados

Criar tabelas locais:

```powershell
.\.venv\Scripts\python.exe .\tools\create_db_tables.py
```

Acessar pelo Adminer:

```text
URL: http://localhost:8187
Sistema: MySQL / MariaDB
Servidor: mariadb
Usuario: valor de MARIADB_USER no .env
Senha: valor de MARIADB_PASSWORD no .env
Base de dados: valor de MARIADB_DATABASE no .env
```

## Git

Antes de commit/push:

```powershell
git status --short
git ls-files | Select-String -Pattern "\.env|\.venv|backups|aplicar_"
.\.venv\Scripts\python.exe -m pytest
```

Nao fazer commit automatico a partir de tarefas do Codex.

## Licenca

Projeto privado/proprietario. Todos os direitos reservados, salvo autorizacao expressa da proprietaria do projeto.
