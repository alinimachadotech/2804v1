"""Serviço para persistência de snapshots de chamadas online."""

import logging
from datetime import datetime, timezone

from app.db.session import SessionLocal
from app.models.online_snapshot import (
    OnlineSnapshot,
    OnlineRouterSnapshot,
    OnlineTopClientsSnapshot,
    OnlineTopRoutesSnapshot,
)
from app.schemas.online_calls import OnlineAggregateAllRoutersOut

logger = logging.getLogger(__name__)


def save_online_snapshot(data: OnlineAggregateAllRoutersOut) -> bool:
    """Salva snapshot agregado de chamadas online em MariaDB.
    
    Salva:
    - Resumo geral (OnlineSnapshot)
    - Resumo por router (OnlineRouterSnapshot)
    - Top 20 clientes (OnlineTopClientsSnapshot)
    - Top 20 rotas (OnlineTopRoutesSnapshot)
    
    Args:
        data: Dados agregados de chamadas online
        
    Returns:
        True se bem-sucedido, False em caso de erro
    """
    try:
        session = SessionLocal()
        
        # Criar snapshot agregado
        snapshot = OnlineSnapshot(
            collected_at=datetime.now(timezone.utc),
            total=data.total,
            ringing=data.ringing,
            talking=data.talking,
            clients_count=data.clients_count,
            routes_count=data.routes_count,
            servers_count=data.servers_count,
            routers_ok=sum(1 for r in data.routers if r.status == "ok"),
            routers_failed=sum(1 for r in data.routers if r.status != "ok"),
        )
        
        session.add(snapshot)
        session.flush()  # Gera o ID do snapshot
        
        # Salvar resumos por router
        for router in data.routers:
            router_snapshot = OnlineRouterSnapshot(
                snapshot_id=snapshot.id,
                router_id=router.router_id,
                total=router.total,
                ringing=router.ringing,
                talking=router.talking,
                status=router.status,
                error_type=None,  # Será preenchido se houver falha
            )
            session.add(router_snapshot)
        
        # Salvar falhas de routers (se houver)
        for failure in data.failures:
            router_snapshot = OnlineRouterSnapshot(
                snapshot_id=snapshot.id,
                router_id=failure.router_id,
                total=0,
                ringing=0,
                talking=0,
                status="failed",
                error_type=_extract_error_type(failure.error),
            )
            session.add(router_snapshot)
        
        # Salvar top 20 clientes
        for position, client in enumerate(data.top_clients[:20], start=1):
            client_snapshot = OnlineTopClientsSnapshot(
                snapshot_id=snapshot.id,
                client_name=client.name,
                total=client.total,
                ringing=client.ringing,
                talking=client.talking,
                position=position,
            )
            session.add(client_snapshot)
        
        # Salvar top 20 rotas
        for position, route in enumerate(data.top_routes[:20], start=1):
            route_snapshot = OnlineTopRoutesSnapshot(
                snapshot_id=snapshot.id,
                route_name=route.route_name,
                total=route.total,
                ringing=route.ringing,
                talking=route.talking,
                position=position,
            )
            session.add(route_snapshot)
        
        session.commit()
        session.close()
        
        logger.debug(f"Snapshot #{snapshot.id} salvo com sucesso")
        return True
    
    except Exception as exc:
        logger.warning(f"Erro ao salvar snapshot: {exc}")
        try:
            session.rollback()
            session.close()
        except Exception:
            pass
        return False


def _extract_error_type(error_message: str) -> str:
    """Extrai tipo de erro de forma segura.
    
    Args:
        error_message: Mensagem de erro completa
        
    Returns:
        Tipo de erro (máximo 100 caracteres, sem dados sensíveis)
    """
    # Retira dados sensíveis e limita tamanho
    message = str(error_message)[:100]
    
    # Remover possíveis dados sensíveis
    for sensitive in ["token", "key", "password", "secret", "ip", "192", "10.", "172.", "127."]:
        if sensitive.lower() in message.lower():
            message = f"[sensível: {sensitive}]"
            break
    
    return message
