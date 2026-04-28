API FastAPI para centralizar operações técnicas e operacionais relacionadas a múltiplos routers NextRouter C4 SoftSwitch.

O objetivo do projeto é evoluir para uma base modular, segura e observável, com persistência em MariaDB, métricas para Prometheus, dashboards no Grafana e contratos de API preparados para um frontend futuro.

> Projeto privado/proprietário. Não publique credenciais, tokens, IPs sensíveis ou arquivos `.env`.

---

## Status atual

Base local funcionando com:

- FastAPI
- MariaDB
- SQLAlchemy
- Adminer
- Prometheus
- Grafana
- Docker Compose para serviços de apoio
- Rotas versionadas em `/api/v1`
- Healthcheck e readiness com banco
- Schema inicial no MariaDB

---

## Estrutura do projeto

```text
app/
  api/
  core/
  db/
  models/
  routes/
docker/
  docker-compose.monitoring.yml
  prometheus/
  grafana/
tests/
tools/
.env.example
.gitignore
README.md
requirements.txt
```

---

## Requisitos locais

Ambiente principal de desenvolvimento:

- Windows
- PowerShell
- VS Code
- Docker Desktop
- Python
- Git

Validar Docker:

```powershell
docker ps
```

Se o Docker estiver funcionando, o comando deve listar containers ou retornar uma tabela vazia sem erro.

---

## Configuração do ambiente

Copie o arquivo de exemplo:

```powershell
Copy-Item .env.example .env
```

Edite o `.env` local:

```powershell
notepad .env
```

Nunca publique o arquivo `.env`.

O arquivo versionado correto é apenas:

```text
.env.example
```

---

## Subir MariaDB, Adminer, Prometheus e Grafana

Na raiz do projeto:

```powershell
cd C:\dev\gerax_manager

docker compose --env-file .\.env -f .\docker\docker-compose.monitoring.yml up -d
```

Verificar containers:

```powershell
docker compose --env-file .\.env -f .\docker\docker-compose.monitoring.yml ps
```

Serviços locais esperados:

```text
MariaDB     localhost:3317
Adminer     http://localhost:8187
Prometheus  http://localhost:9090
Grafana     http://localhost:3180
```

A porta `3317` é do banco MariaDB. Ela não deve ser aberta no navegador.

---

## Rodar a API localmente

Criar ambiente virtual:

```powershell
python -m venv .venv
```

Instalar dependências sem precisar ativar o ambiente:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

Rodar a API:

```powershell
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload
```

A API ficará disponível em:

```text
http://127.0.0.1:8000
```

Swagger/OpenAPI:

```text
http://127.0.0.1:8000/docs
```

---

## Endpoints principais

Rotas básicas:

```text
GET /
GET /ping
GET /health
```

Rotas versionadas:

```text
GET /api/v1/health
GET /api/v1/ready
```

Métricas Prometheus:

```text
GET /metrics
```

---

## Testes rápidos

API:

```powershell
Invoke-RestMethod http://127.0.0.1:8000/
Invoke-RestMethod http://127.0.0.1:8000/ping
Invoke-RestMethod http://127.0.0.1:8000/api/v1/health
Invoke-RestMethod http://127.0.0.1:8000/api/v1/ready
```

Métricas:

```powershell
Invoke-WebRequest http://127.0.0.1:8000/metrics
```

Testes automatizados:

```powershell
.\.venv\Scripts\python.exe -m pytest
```

---

## Banco de dados

O banco local é MariaDB.

Criar tabelas locais:

```powershell
.\.venv\Scripts\python.exe .\tools\create_db_tables.py
```

Tabelas iniciais esperadas:

```text
routers
sync_runs
online_router_snapshots
```

Acessar pelo Adminer:

```text
URL: http://localhost:8187
Sistema: MySQL / MariaDB
Servidor: mariadb
Usuário: valor de MARIADB_USER no .env
Senha: valor de MARIADB_PASSWORD no .env
Base de dados: valor de MARIADB_DATABASE no .env
```

---

## Observabilidade

### Prometheus

URL local:

```text
http://localhost:9090
```

Verificar targets:

```text
http://localhost:9090/targets
```

A API deve aparecer como `UP`.

### Grafana

URL local:

```text
http://localhost:3180
```

O Grafana deve usar o Prometheus como fonte de dados.

Dentro do Docker, a URL do Prometheus para o Grafana é:

```text
http://prometheus:9090
```

Não coloque tokens de routers no Grafana.

---

## Segurança

Regras obrigatórias:

- Nunca versionar `.env`.
- Nunca publicar tokens reais.
- Nunca publicar senhas reais.
- Nunca publicar IPs sensíveis.
- Nunca colocar tokens dos routers no Grafana.
- Nunca expor a API publicamente sem autenticação, HTTPS, CORS controlado e política mínima de acesso.
- Separar métricas técnicas de dados sensíveis de clientes.
- Usar `.env.example` apenas com valores fictícios.

Verificar arquivos sensíveis no Git:

```powershell
git ls-files | Select-String -Pattern "\.env|\.venv|backups|aplicar_"
```

A única saída aceitável relacionada a `.env` é:

```text
.env.example
```

---

## Git

Branch principal do projeto:

```text
principal
```

Fluxo básico:

```powershell
git status
git add .
git commit -m "mensagem do commit"
git push
```

Antes de cada push, conferir:

```powershell
git status --short
git ls-files | Select-String -Pattern "\.env|\.venv|backups|aplicar_"
```

---

## Roadmap

### Fase 1 — Segurança e base

- Validar `.gitignore`
- Garantir `.env.example` sem segredos
- Organizar estrutura de pastas
- Criar README técnico

### Fase 2 — Banco e persistência

- Validar MariaDB
- Criar models SQLAlchemy
- Criar tabelas base
- Evoluir de `create_all` para Alembic

### Fase 3 — Observabilidade

- Expor `/health`
- Expor `/api/v1/ready`
- Expor `/metrics`
- Integrar Prometheus
- Integrar Grafana

### Fase 4 — Frontend-ready

- Padronizar schemas Pydantic
- Versionar endpoints
- Criar filtros, paginação e ordenação
- Preparar CORS controlado

### Fase 5 — Produção

- Criar Dockerfile da API
- Criar compose de produção
- Adicionar autenticação
- Adicionar logs estruturados
- Planejar backup e restore
- Preparar deploy Linux/Debian/Proxmox

---

## Licença

Projeto privado/proprietário.

Todos os direitos reservados, salvo autorização expressa da proprietária do projeto.
