"""Schemas para chamadas online."""

from typing import Optional

from pydantic import BaseModel


class OnlineClientSummaryOut(BaseModel):
    """Resumo de cliente em agregação."""
    name: str
    total: int
    ringing: int
    talking: int


class OnlineRouterSummaryOut(BaseModel):
    """Resumo de um router."""
    router_id: int
    router_name: str
    total: int
    ringing: int
    talking: int
    status: str  # "success" ou "failed"


class OnlineFailureOut(BaseModel):
    """Falha ao obter dados de um router."""
    router_id: int
    router_name: str
    error: str


class OnlineRouteMetricOut(BaseModel):
    """Métrica detalhada de uma rota."""
    router_id: int
    router_name: str
    route_id: str
    route_name: str
    total: int
    ringing: int
    talking: int
    asr: Optional[float]
    acd: Optional[str]
    pdd: Optional[str]
    pdd_int: int
    alerta_pdd: int
    total_calls: int
    talk_time: int
    pdd_alert: bool
    asr_alert: bool


class OnlineTopRouteOut(BaseModel):
    """Top rota consolidada."""
    route_name: str
    total: int
    ringing: int
    talking: int
    avg_asr: Optional[float]
    max_pdd_int: int


class OnlineServerMetricOut(BaseModel):
    """Métrica detalhada de um servidor."""
    router_id: int
    router_name: str
    server_ip: str
    total: int
    cps: Optional[str]
    chamando: int
    falando: int


class OnlineAggregateAllRoutersOut(BaseModel):
    """Agregação de todos os routers."""
    total: int
    ringing: int
    talking: int
    clients_count: int
    routes_count: int
    servers_count: int
    top_clients: list[OnlineClientSummaryOut]
    routers: list[OnlineRouterSummaryOut]
    failures: list[OnlineFailureOut]
    routes: list[OnlineRouteMetricOut]
    top_routes: list[OnlineTopRouteOut]
    top_routes_by_router: list[OnlineRouteMetricOut]
    servers: list[OnlineServerMetricOut]
