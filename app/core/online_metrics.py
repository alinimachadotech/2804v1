"""Métricas Prometheus para monitoramento de chamadas online."""

import time
from prometheus_client import Counter, Gauge, Histogram

# Métricas de estado atual
gerax_online_total_current = Gauge(
    "gerax_online_total_current",
    "Número total de chamadas online no momento",
)

gerax_online_ringing_current = Gauge(
    "gerax_online_ringing_current",
    "Número de chamadas tocando no momento",
)

gerax_online_talking_current = Gauge(
    "gerax_online_talking_current",
    "Número de chamadas em conversa no momento",
)

gerax_online_clients_count_current = Gauge(
    "gerax_online_clients_count_current",
    "Número de clientes com chamadas online",
)

gerax_online_routes_count_current = Gauge(
    "gerax_online_routes_count_current",
    "Número de rotas com chamadas online",
)

gerax_online_servers_count_current = Gauge(
    "gerax_online_servers_count_current",
    "Número de servidores com chamadas online",
)

# Métrica de status por router (sem dados sensíveis)
gerax_online_router_status = Gauge(
    "gerax_online_router_status",
    "Status do router (1=online/sucesso, 0=offline/falha)",
    labelnames=["router_id"],
)

# Métricas de coleta
gerax_online_collection_success_total = Counter(
    "gerax_online_collection_success_total",
    "Total de coletas bem-sucedidas de dados online",
)

gerax_online_collection_failure_total = Counter(
    "gerax_online_collection_failure_total",
    "Total de coletas falhadas de dados online",
)

gerax_online_last_collection_timestamp = Gauge(
    "gerax_online_last_collection_timestamp",
    "Timestamp da última coleta de dados online (segundos desde epoch)",
)


def update_online_metrics(data: dict) -> None:
    """Atualiza métricas Prometheus com dados de agregação.
    
    Args:
        data: Dicionário com dados de OnlineAggregateAllRoutersOut
    """
    try:
        # Métricas de estado
        gerax_online_total_current.set(data.get("total", 0))
        gerax_online_ringing_current.set(data.get("ringing", 0))
        gerax_online_talking_current.set(data.get("talking", 0))
        gerax_online_clients_count_current.set(data.get("clients_count", 0))
        gerax_online_routes_count_current.set(data.get("routes_count", 0))
        gerax_online_servers_count_current.set(data.get("servers_count", 0))
        
        # Status por router
        routers = data.get("routers", [])
        for router in routers:
            router_id = str(router.get("router_id", "unknown"))
            status = 1 if router.get("status") == "ok" else 0
            gerax_online_router_status.labels(router_id=router_id).set(status)
        
        # Timestamp da coleta
        gerax_online_last_collection_timestamp.set(time.time())
        
        # Contabiliza sucesso
        gerax_online_collection_success_total.inc()
    except Exception as exc:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Erro ao atualizar métricas online: {exc}")
        gerax_online_collection_failure_total.inc()
