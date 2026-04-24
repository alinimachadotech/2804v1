from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]

REQUIRED_PATHS = [
    "app/__init__.py",
    "app/main.py",

    "app/core/__init__.py",
    "app/core/settings.py",
    "app/core/logging.py",
    "app/core/security.py",
    "app/core/crypto.py",
    "app/core/errors.py",
    "app/core/constants.py",

    "app/db/__init__.py",
    "app/db/session.py",
    "app/db/base.py",
    "app/db/migrations_placeholder.txt",

    "app/models/__init__.py",
    "app/models/router.py",
    "app/models/customer.py",
    "app/models/balance.py",
    "app/models/online_calls.py",
    "app/models/audit.py",
    "app/models/api_log.py",
    "app/models/financial.py",
    "app/models/approval.py",

    "app/schemas/__init__.py",
    "app/schemas/router.py",
    "app/schemas/customer.py",
    "app/schemas/balance.py",
    "app/schemas/online_calls.py",
    "app/schemas/reports.py",
    "app/schemas/financial.py",
    "app/schemas/audit.py",
    "app/schemas/common.py",

    "app/repositories/__init__.py",
    "app/repositories/router_repository.py",
    "app/repositories/customer_repository.py",
    "app/repositories/balance_repository.py",
    "app/repositories/online_repository.py",
    "app/repositories/audit_repository.py",
    "app/repositories/api_log_repository.py",
    "app/repositories/financial_repository.py",

    "app/services/__init__.py",
    "app/services/router_service.py",
    "app/services/customer_service.py",
    "app/services/balance_service.py",
    "app/services/online_calls_service.py",
    "app/services/reports_service.py",
    "app/services/financial_service.py",
    "app/services/approval_service.py",
    "app/services/audit_service.py",

    "app/integrations/__init__.py",
    "app/integrations/nextrouter/__init__.py",
    "app/integrations/nextrouter/client.py",
    "app/integrations/nextrouter/endpoints.py",
    "app/integrations/nextrouter/parser.py",
    "app/integrations/nextrouter/exceptions.py",
    "app/integrations/nextrouter/rate_limit.py",

    "app/api/__init__.py",
    "app/api/v1/__init__.py",
    "app/api/v1/router.py",
    "app/api/v1/endpoints/__init__.py",
    "app/api/v1/endpoints/health.py",
    "app/api/v1/endpoints/routers.py",
    "app/api/v1/endpoints/customers.py",
    "app/api/v1/endpoints/balances.py",
    "app/api/v1/endpoints/online_calls.py",
    "app/api/v1/endpoints/reports.py",
    "app/api/v1/endpoints/financial.py",
    "app/api/v1/endpoints/admin.py",

    "app/workers/__init__.py",
    "app/workers/scheduler.py",
    "app/workers/collectors/__init__.py",
    "app/workers/collectors/customers_collector.py",
    "app/workers/collectors/balances_collector.py",
    "app/workers/collectors/online_calls_collector.py",
    "app/workers/collectors/cdr_collector.py",
    "app/workers/collectors/profit_customers_collector.py",
    "app/workers/collectors/profit_gateways_collector.py",

    "app/utils/__init__.py",
    "app/utils/money.py",
    "app/utils/datetime.py",
    "app/utils/masking.py",
    "app/utils/pagination.py",

    "tests/__init__.py",
    "tests/test_health.py",
    "tests/test_money_parser.py",
    "tests/test_router_service.py",
    "tests/test_nextrouter_parser.py",

    "docker/Dockerfile",
    "docker/entrypoint.sh",
    "docker-compose.yml",
    "requirements.txt",
    ".env.example",
    ".gitignore",
    "README.md",
    "alembic.ini",
]


def main() -> int:
    missing = []

    for relative_path in REQUIRED_PATHS:
        path = ROOT / relative_path
        if not path.exists():
            missing.append(relative_path)

    if missing:
        print("❌ Estrutura inválida. Arquivos/pastas ausentes:")
        for item in missing:
            print(f" - {item}")
        return 1

    print("✅ Estrutura válida. Todos os arquivos obrigatórios existem.")
    return 0


if __name__ == "__main__":
    sys.exit(main())