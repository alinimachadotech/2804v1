# AGENTS.md — api-gerax / Gerax Hub

## Contexto do projeto

Este repositório é o backend FastAPI do api-gerax/Gerax Hub.

Objetivo:
Construir uma camada segura, modular e observável para integrar múltiplos routers NextRouter C4 SoftSwitch, entregando dados para frontend Vue, Grafana, Prometheus e rotinas internas de operação.

O projeto deve priorizar:
- segurança;
- arquitetura modular;
- integração com múltiplos routers;
- logs sem vazamento de credenciais;
- Redis cache;
- MariaDB;
- Prometheus metrics;
- contratos Pydantic claros;
- testes com mocks.

## Regras obrigatórias de segurança

Nunca:
- versionar `.env`;
- imprimir token, key, senha ou URL completa contendo credenciais;
- colocar token/key no frontend;
- colocar token/key no Grafana;
- commitar IPs sensíveis reais em exemplos;
- usar `verify=False` fixo em produção;
- fazer mudança grande sem teste básico.

Sempre:
- usar `.env.example` com valores fictícios;
- mascarar segredos em logs;
- usar `Decimal` para valores financeiros;
- usar paginação `start` e `limit`;
- tratar erros 400, 403, 404, 413, 422, 429 e 5xx;
- manter compatibilidade com a estrutura atual.

## Comandos locais

Instalar dependências:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt