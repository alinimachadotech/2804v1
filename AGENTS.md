# AGENTS.md - api-gerax / Gerax Hub

## Contexto do projeto

Este repositorio e o backend FastAPI do api-gerax/Gerax Hub.

Objetivo:
Construir uma camada segura, modular, observavel e read-only para consultar multiplos routers NextRouter C4 SoftSwitch, entregando dados normalizados para frontend Vue, Grafana, Prometheus e rotinas internas de operacao.

O projeto deve priorizar:
- seguranca;
- arquitetura modular;
- integracao com multiplos routers;
- logs sem vazamento de credenciais;
- Redis cache;
- MariaDB;
- Prometheus metrics;
- contratos Pydantic claros;
- testes com mocks.

## Escopo read-only obrigatorio

O api-gerax deve consultar, normalizar, cachear, historizar e observar dados. Ele nao deve alterar dados no NextRouter.

Nunca implementar, expor ou chamar:
- `POST /api/statusCustomer`;
- `POST /api/manageCredit`;
- `DELETE /api/onlineCalls`;
- ativacao de cliente;
- desativacao de cliente;
- credito de saldo;
- debito de saldo;
- definicao de saldo;
- encerramento de chamada.

Todas as integracoes NextRouter no `NextRouterClient` devem usar `GET`.

## Metodos permitidos no NextRouterClient

- `get_customer_balance`
- `get_customer`
- `get_credit_history`
- `get_online_calls`
- `get_online_calls_aggregate`
- `get_cdr`
- `get_cdr_disconnection`
- `get_cdr_sipcodes`
- `get_profit_customers`
- `get_profit_gateways`
- `get_contacts`

## Regras obrigatorias de seguranca

Nunca:
- versionar `.env`;
- imprimir token, key, senha ou URL completa contendo credenciais;
- colocar token/key do NextRouter no frontend;
- colocar token/key do NextRouter no Grafana;
- commitar IPs sensiveis reais em exemplos;
- usar `verify=False` fixo em producao;
- fazer mudanca grande sem teste basico.

Sempre:
- usar `.env.example` com valores ficticios;
- mascarar segredos em logs;
- usar `Decimal` para valores financeiros;
- usar paginacao `start` e `limit`;
- tratar erros 400, 403, 404, 413, 422, 429 e 5xx;
- manter compatibilidade com a estrutura atual.

## Comandos locais

Instalar dependencias:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

Rodar testes:

```powershell
.\.venv\Scripts\python.exe -m pytest
```
