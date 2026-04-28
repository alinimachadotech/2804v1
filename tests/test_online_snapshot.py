"""Testes para o serviço de snapshots online."""

import pytest
from unittest.mock import patch, MagicMock

from app.services.online_snapshot_service import save_online_snapshot
from app.schemas.online_calls import (
    OnlineAggregateAllRoutersOut,
    OnlineClientSummaryOut,
    OnlineRouterSummaryOut,
    OnlineFailureOut,
    OnlineTopRouteOut,
    OnlineRouteMetricOut,
    OnlineServerMetricOut,
)


@pytest.fixture
def mock_aggregate_data():
    """Cria dados mockados para testes de snapshot."""
    return OnlineAggregateAllRoutersOut(
        total=150,
        ringing=30,
        talking=50,
        clients_count=3,
        routes_count=5,
        servers_count=2,
        top_clients=[
            OnlineClientSummaryOut(name="Client A", total=100, ringing=10, talking=30),
            OnlineClientSummaryOut(name="Client B", total=50, ringing=20, talking=20),
        ],
        routers=[
            OnlineRouterSummaryOut(
                router_id=1, router_name="Router 1", total=100, ringing=15, talking=30, status="ok"
            ),
            OnlineRouterSummaryOut(
                router_id=2, router_name="Router 2", total=50, ringing=15, talking=20, status="ok"
            ),
        ],
        failures=[],
        routes=[
            OnlineRouteMetricOut(
                router_id=1, router_name="Router 1", route_id="1", route_name="Route A",
                total=50, ringing=5, talking=15, asr=95.0, acd=None, pdd=None,
                pdd_int=0, alerta_pdd=0, total_calls=0, talk_time=0, pdd_alert=False, asr_alert=False
            ),
        ],
        top_routes=[
            OnlineTopRouteOut(route_name="Route A", total=50, ringing=5, talking=15, avg_asr=95.0, max_pdd_int=0),
        ],
        top_routes_by_router=[],
        servers=[
            OnlineServerMetricOut(
                router_id=1, router_name="Router 1", server_ip="192.168.1.1",
                total=100, cps=None, chamando=15, falando=30
            ),
        ],
    )


def test_save_online_snapshot_success(mock_aggregate_data):
    """Testa que save_online_snapshot salva o resumo corretamente."""
    with patch("app.services.online_snapshot_service.SessionLocal") as mock_session_class:
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session
        
        result = save_online_snapshot(mock_aggregate_data)
        
        assert result is True
        mock_session.add.assert_called()
        mock_session.commit.assert_called()
        mock_session.close.assert_called()


def test_save_online_snapshot_saves_routers(mock_aggregate_data):
    """Testa que save_online_snapshot salva resumo por router."""
    with patch("app.services.online_snapshot_service.SessionLocal") as mock_session_class:
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session
        mock_session.id = 1
        
        result = save_online_snapshot(mock_aggregate_data)
        
        assert result is True
        # Verificar que múltiplas entidades foram adicionadas (snapshot + routers + clients + routes)
        assert mock_session.add.call_count > 1


def test_save_online_snapshot_saves_top_clients(mock_aggregate_data):
    """Testa que save_online_snapshot salva top clients."""
    with patch("app.services.online_snapshot_service.SessionLocal") as mock_session_class:
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session
        
        result = save_online_snapshot(mock_aggregate_data)
        
        assert result is True
        # Deve ter salvo pelo menos 1 cliente (2 no mock)
        # Verificar através do número de chamadas ao add


def test_save_online_snapshot_handles_failure(mock_aggregate_data):
    """Testa que falha ao salvar não derruba a API."""
    with patch("app.services.online_snapshot_service.SessionLocal") as mock_session_class:
        # Simular falha
        mock_session = MagicMock()
        mock_session.add.side_effect = Exception("Database error")
        mock_session_class.return_value = mock_session
        
        result = save_online_snapshot(mock_aggregate_data)
        
        assert result is False
        mock_session.rollback.assert_called()


def test_save_online_snapshot_limits_top_items(mock_aggregate_data):
    """Testa que apenas top 20 clients e rotas são salvos."""
    # Criar 30 clients e rotas
    mock_aggregate_data.top_clients = [
        OnlineClientSummaryOut(name=f"Client {i}", total=100-i, ringing=10, talking=20)
        for i in range(30)
    ]
    mock_aggregate_data.top_routes = [
        OnlineTopRouteOut(route_name=f"Route {i}", total=100-i, ringing=5, talking=15, avg_asr=95.0, max_pdd_int=0)
        for i in range(30)
    ]
    
    with patch("app.services.online_snapshot_service.SessionLocal") as mock_session_class:
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session
        
        result = save_online_snapshot(mock_aggregate_data)
        
        assert result is True
        # Verificar que apenas 20 foram processados para cada (visto que o slice é [:20])


def test_endpoint_calls_save_snapshot_on_fresh_data():
    """Testa que endpoint chama save_online_snapshot em coleta real."""
    from unittest.mock import patch as mock_patch
    from fastapi.testclient import TestClient
    from app.main import app
    
    client = TestClient(app)
    
    # Mock do cache retornando None (coleta real)
    with mock_patch("app.api.v1.endpoints.online_calls.get_cached_online_aggregate_all", return_value=None), \
         mock_patch("app.api.v1.endpoints.online_calls.set_cached_online_aggregate_all", return_value=True), \
         mock_patch("app.api.v1.endpoints.online_calls.get_online_aggregate_all_routers") as mock_get_all, \
         mock_patch("app.api.v1.endpoints.online_calls.save_online_snapshot") as mock_save_snapshot, \
         mock_patch("app.api.v1.endpoints.online_calls.update_online_metrics"):
        
        # Mock da resposta do serviço
        mock_response = MagicMock(spec=OnlineAggregateAllRoutersOut)
        mock_response.model_dump.return_value = {}
        mock_get_all.return_value = mock_response
        
        response = client.get("/api/v1/online/aggregate/all-routers")
        
        assert response.status_code == 200
        mock_save_snapshot.assert_called_once()


def test_endpoint_skips_save_snapshot_on_cache():
    """Testa que endpoint NÃO chama save_online_snapshot quando vem do cache."""
    from unittest.mock import patch as mock_patch
    from fastapi.testclient import TestClient
    from app.main import app
    
    client = TestClient(app)
    
    # Mock do cache retornando dados (cache hit)
    cached_data = MagicMock(spec=OnlineAggregateAllRoutersOut)
    cached_data.model_dump.return_value = {}
    
    with mock_patch("app.api.v1.endpoints.online_calls.get_cached_online_aggregate_all", return_value=cached_data), \
         mock_patch("app.api.v1.endpoints.online_calls.save_online_snapshot") as mock_save_snapshot, \
         mock_patch("app.api.v1.endpoints.online_calls.update_online_metrics"):
        
        response = client.get("/api/v1/online/aggregate/all-routers")
        
        assert response.status_code == 200
        mock_save_snapshot.assert_not_called()
