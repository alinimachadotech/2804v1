import importlib

from app.db.base import Base
from app.models.financial import (
    HistoricoSaldosDiario,
    MargemLucroOperacional,
    RelatorioAssinantesDiario,
    RelatorioAssinantesMensal,
    RelatorioAssinantesPorPeriodo,
    RelatorioAssinantesQuinzenal,
    RelatorioAssinantesSemanal,
    RelatorioRotasDiario,
    SipcodesAgregado,
    TodosAssinantes,
    TodosAssinantesHist,
    VariacoesAssinantes,
    VwPriorizeHist,
)


def test_financial_models_importable() -> None:
    assert TodosAssinantes.__tablename__ == "todos_assinantes"
    assert TodosAssinantesHist.__tablename__ == "todos_assinantes_hist"
    assert RelatorioAssinantesDiario.__tablename__ == "relatorio_assinantes_diario"
    assert RelatorioAssinantesSemanal.__tablename__ == "relatorio_assinantes_semanal"
    assert RelatorioAssinantesQuinzenal.__tablename__ == "relatorio_assinantes_quinzenal"
    assert RelatorioAssinantesMensal.__tablename__ == "relatorio_assinantes_mensal"
    assert RelatorioAssinantesPorPeriodo.__tablename__ == "relatorio_assinantes_por_periodo"
    assert RelatorioRotasDiario.__tablename__ == "relatorio_rotas_diario"
    assert HistoricoSaldosDiario.__tablename__ == "historico_saldos_diario"
    assert MargemLucroOperacional.__tablename__ == "margem_lucro_operacional"
    assert SipcodesAgregado.__tablename__ == "sipcodes_agregado"
    assert VariacoesAssinantes.__tablename__ == "variacoes_assinantes"
    assert VwPriorizeHist.__tablename__ == "vw_priorize_hist"


def test_financial_tables_registered_in_metadata() -> None:
    import app.models  # noqa: F401
    import tools.create_db_tables as create_db_tables

    importlib.reload(create_db_tables)

    registered_tables = set(Base.metadata.tables)
    expected_tables = {
        "todos_assinantes",
        "todos_assinantes_hist",
        "relatorio_assinantes_diario",
        "relatorio_assinantes_semanal",
        "relatorio_assinantes_quinzenal",
        "relatorio_assinantes_mensal",
        "relatorio_assinantes_por_periodo",
        "relatorio_rotas_diario",
        "historico_saldos_diario",
        "margem_lucro_operacional",
        "sipcodes_agregado",
        "variacoes_assinantes",
        "vw_priorize_hist",
    }

    assert expected_tables <= registered_tables
