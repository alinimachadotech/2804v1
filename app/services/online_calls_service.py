"""Serviço para gerenciar chamadas online."""

import logging
from collections import defaultdict

from app.integrations.nextrouter.client import NextRouterClient
from app.integrations.nextrouter.exceptions import NextRouterError
from app.schemas.online_calls import OnlineAggregateAllRoutersOut
from app.services.router_service import (
    get_router_by_id,
    get_router_secret_by_router_id,
    list_routers,
)
from app.core.settings import settings


logger = logging.getLogger(__name__)


def to_int(value) -> int:
    """Converte um valor para int de forma segura.
    
    Aceita:
    - int
    - float
    - string numérica
    - None
    - string vazia
    
    Retorna 0 quando não conseguir converter.
    """
    if value is None or value == "":
        return 0
    
    if isinstance(value, int):
        return value
    
    if isinstance(value, float):
        return int(value)
    
    if isinstance(value, str):
        try:
            return int(float(value))
        except (ValueError, TypeError):
            return 0
    
    return 0


def normalize_route_item(item: dict, router) -> dict:
    """Normaliza um item de rota do NextRouter.
    
    Args:
        item: Dicionário com dados da rota
        router: Objeto router
        
    Returns:
        Dicionário normalizado
    """
    route_id = str(item.get("id", ""))
    route_name = item.get("cliente") or item.get("name", "")
    
    ringing = to_int(item.get("chamando")) or to_int(item.get("ringing")) or to_int(item.get("tocando"))
    talking = to_int(item.get("falando")) or to_int(item.get("talking")) or to_int(item.get("conversando"))
    total = to_int(item.get("total"))
    
    asr = item.get("asr")
    if asr is not None:
        try:
            asr = float(asr)
        except (ValueError, TypeError):
            asr = None
    
    acd = item.get("acd")
    pdd = item.get("pdd")
    pdd_int = to_int(item.get("pdd_int"))
    alerta_pdd = to_int(item.get("alerta_pdd"))
    total_calls = to_int(item.get("total_calls"))
    talk_time = to_int(item.get("talk_time"))
    
    pdd_alert = pdd_int > alerta_pdd if pdd_int and alerta_pdd else False
    asr_alert = asr is not None and asr < 30
    
    return {
        "router_id": router.id,
        "router_name": router.name,
        "route_id": route_id,
        "route_name": route_name,
        "total": total,
        "ringing": ringing,
        "talking": talking,
        "asr": asr,
        "acd": acd,
        "pdd": pdd,
        "pdd_int": pdd_int,
        "alerta_pdd": alerta_pdd,
        "total_calls": total_calls,
        "talk_time": talk_time,
        "pdd_alert": pdd_alert,
        "asr_alert": asr_alert,
    }


def build_top_routes(routes: list[dict]) -> list[dict]:
    """Constrói top routes consolidadas.
    
    Args:
        routes: Lista de rotas normalizadas
        
    Returns:
        Lista de top routes consolidadas
    """
    from collections import defaultdict
    
    routes_dict = defaultdict(lambda: {
        "total": 0,
        "ringing": 0,
        "talking": 0,
        "asr_values": [],
        "max_pdd_int": 0,
    })
    
    for route in routes:
        name = route["route_name"]
        routes_dict[name]["total"] += route["total"]
        routes_dict[name]["ringing"] += route["ringing"]
        routes_dict[name]["talking"] += route["talking"]
        
        if route["asr"] is not None:
            routes_dict[name]["asr_values"].append(route["asr"])
        
        routes_dict[name]["max_pdd_int"] = max(routes_dict[name]["max_pdd_int"], route["pdd_int"])
    
    top_routes = []
    for name, data in routes_dict.items():
        avg_asr = None
        if data["asr_values"]:
            avg_asr = sum(data["asr_values"]) / len(data["asr_values"])
        
        top_routes.append({
            "route_name": name,
            "total": data["total"],
            "ringing": data["ringing"],
            "talking": data["talking"],
            "avg_asr": avg_asr,
            "max_pdd_int": data["max_pdd_int"],
        })
    
    top_routes.sort(key=lambda x: x["total"], reverse=True)
    return top_routes[:20]


def normalize_server_item(item: dict, router) -> dict:
    """Normaliza um item de servidor do NextRouter.
    
    Args:
        item: Dicionário com dados do servidor
        router: Objeto router
        
    Returns:
        Dicionário normalizado
    """
    server_ip = str(item.get("server_ip") or item.get("ip", ""))
    total = to_int(item.get("total"))
    cps = item.get("cps")
    chamando = to_int(item.get("chamando"))
    falando = to_int(item.get("falando"))
    
    return {
        "router_id": router.id,
        "router_name": router.name,
        "server_ip": server_ip,
        "total": total,
        "cps": cps,
        "chamando": chamando,
        "falando": falando,
    }


def get_online_aggregate_by_router_id(router_id: int) -> dict:
    """Busca agregação de chamadas online de um router.
    
    Args:
        router_id: ID do router
        
    Returns:
        Dicionário com dados de agregação de chamadas online
        
    Raises:
        ValueError: Router não encontrado
        NextRouterError: Erro ao comunicar com NextRouter
    """
    router_config = get_router_secret_by_router_id(router_id)
    
    if not router_config:
        raise ValueError(f"Router {router_id} não encontrado")
    
    client = NextRouterClient(
        base_url=f"https://{router_config.ip}",
        timeout=settings.router_request_timeout_seconds,
    )
    
    token = router_config.token.get_secret_value()
    key = router_config.key.get_secret_value()
    
    return client.get_online_calls_aggregate(token, key)


def get_online_aggregate_all_routers() -> OnlineAggregateAllRoutersOut:
    """Busca agregação de chamadas online de todos os routers.
    
    Se um router falhar, registra e continua com os outros.
    
    Returns:
        OnlineAggregateAllRoutersOut com dados consolidados
    """
    routers = list_routers()
    
    # Acumuladores para campos numéricos
    total_total = 0
    total_ringing = 0
    total_talking = 0
    
    # Acumuladores para listas
    all_clients_list = []
    all_routes_list = []
    all_servers_list = []
    
    # Listas normalizadas
    normalized_routes = []
    normalized_servers = []
    
    # Consolidação de clientes por "cliente"
    clients_dict: dict[str, dict] = defaultdict(lambda: {
        "total": 0,
        "ringing": 0,
        "talking": 0,
    })
    
    # Resultados por router
    routers_summary = []
    failures = []
    
    for router in routers:
        router_id = router.id
        router_name = router.name
        
        try:
            data = get_online_aggregate_by_router_id(router_id)
            
            # Dados do router - campos numéricos
            router_total = data.get("total", 0)
            
            # Normalizar field ringing: tentar ringint primeiro, depois ringing
            router_ringing = data.get("ringint")
            if router_ringing is None:
                router_ringing = data.get("ringing", 0)
            if not isinstance(router_ringing, int):
                router_ringing = 0
            
            router_talking = data.get("talking", 0)
            if not isinstance(router_talking, int):
                router_talking = 0
            
            # Acumula totais numéricos
            total_total += router_total
            total_ringing += router_ringing
            total_talking += router_talking
            
            # Acumula listas (clients, routes, servers podem ser listas)
            clients_list = data.get("clients", [])
            if isinstance(clients_list, list):
                all_clients_list.extend(clients_list)
            
            routes_list = data.get("routes", [])
            if isinstance(routes_list, list):
                all_routes_list.extend(routes_list)
                normalized_routes.extend([normalize_route_item(route, router) for route in routes_list if isinstance(route, dict)])
            
            servers_list = data.get("servers", [])
            if isinstance(servers_list, list):
                all_servers_list.extend(servers_list)
                normalized_servers.extend([normalize_server_item(server, router) for server in servers_list if isinstance(server, dict)])
            
            # Consolidação de clientes com normalização robusta
            if isinstance(clients_list, list):
                for client in clients_list:
                    # Normalizar nome: tentar "cliente" primeiro, depois "name"
                    client_name = client.get("cliente") or client.get("name", "unknown")
                    client_name = str(client_name).strip()
                    if not client_name:
                        client_name = "unknown"
                    
                    # Normalizar total
                    client_total = to_int(client.get("total"))
                    
                    # Normalizar ringing: tentar "chamando", depois "ringing", depois "tocando"
                    client_ringing = to_int(client.get("chamando"))
                    if client_ringing == 0:
                        client_ringing = to_int(client.get("ringing"))
                    if client_ringing == 0:
                        client_ringing = to_int(client.get("tocando"))
                    
                    # Normalizar talking: tentar "falando", depois "talking", depois "conversando"
                    client_talking = to_int(client.get("falando"))
                    if client_talking == 0:
                        client_talking = to_int(client.get("talking"))
                    if client_talking == 0:
                        client_talking = to_int(client.get("conversando"))
                    
                    # Se total for 0 mas ringing/talking existirem, calcular total
                    if client_total == 0 and (client_ringing > 0 or client_talking > 0):
                        client_total = client_ringing + client_talking
                    
                    # Acumular na consolidação
                    clients_dict[client_name]["total"] += client_total
                    clients_dict[client_name]["ringing"] += client_ringing
                    clients_dict[client_name]["talking"] += client_talking
            
            # Resumo do router - apenas erros reais marcam como "failed"
            routers_summary.append({
                "router_id": router_id,
                "router_name": router_name,
                "total": router_total,
                "ringing": router_ringing,
                "talking": router_talking,
                "status": "ok",
            })
        
        except NextRouterError as exc:
            logger.error(f"Erro ao obter dados de {router_name}: {exc}")
            
            failures.append({
                "router_id": router_id,
                "router_name": router_name,
                "error": str(exc),
            })
            
            routers_summary.append({
                "router_id": router_id,
                "router_name": router_name,
                "total": 0,
                "ringing": 0,
                "talking": 0,
                "status": "failed",
            })
        
        except Exception as exc:
            logger.error(f"Erro inesperado em {router_name}: {exc}")
            
            failures.append({
                "router_id": router_id,
                "router_name": router_name,
                "error": f"Erro inesperado: {exc}",
            })
            
            routers_summary.append({
                "router_id": router_id,
                "router_name": router_name,
                "total": 0,
                "ringing": 0,
                "talking": 0,
                "status": "failed",
            })
    
    # Top clients (ordenado por total desc, limitado aos 20 primeiros)
    top_clients = [
        {
            "name": name,
            "total": data["total"],
            "ringing": data["ringing"],
            "talking": data["talking"],
        }
        for name, data in clients_dict.items()
    ]
    top_clients.sort(key=lambda x: x["total"], reverse=True)
    top_clients = top_clients[:20]  # Limitar aos 20 primeiros
    
    # Top routes
    top_routes = build_top_routes(normalized_routes)
    
    # Top routes by router (ordenado por total desc, limitado aos 50 primeiros)
    top_routes_by_router = sorted(normalized_routes, key=lambda x: x["total"], reverse=True)[:50]
    
    # Contadores finais
    total_clients_count = len(all_clients_list)
    total_routes_count = len(all_routes_list)
    total_servers_count = len(all_servers_list)
    
    return OnlineAggregateAllRoutersOut(
        total=total_total,
        ringing=total_ringing,
        talking=total_talking,
        clients_count=total_clients_count,
        routes_count=total_routes_count,
        servers_count=total_servers_count,
        top_clients=top_clients,
        routers=routers_summary,
        failures=failures,
        routes=normalized_routes,
        top_routes=top_routes,
        top_routes_by_router=top_routes_by_router,
        servers=normalized_servers,
    )
