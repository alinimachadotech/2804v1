from datetime import date, datetime

from sqlalchemy import Date, DateTime, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class FinancialMixin:
    router: Mapped[str] = mapped_column(String(120), nullable=True)
    customer_id: Mapped[str] = mapped_column(String(80), nullable=True, index=True)
    customer_name: Mapped[str] = mapped_column(String(200), nullable=True)
    nome_fantasia: Mapped[str] = mapped_column(String(200), nullable=True)
    razao_social: Mapped[str] = mapped_column(String(200), nullable=True)
    status: Mapped[str] = mapped_column(String(80), nullable=True)
    tipo_plano: Mapped[str] = mapped_column(String(120), nullable=True)
    saldo: Mapped[float] = mapped_column(Numeric(18, 4), nullable=True)
    simultaneas: Mapped[int] = mapped_column(Integer, nullable=True)
    usuarios_ativos: Mapped[int] = mapped_column(Integer, nullable=True)
    chamadas: Mapped[int] = mapped_column(Integer, nullable=True)
    duracao_total_seg: Mapped[int] = mapped_column(Integer, nullable=True)
    duracao_media_seg: Mapped[float] = mapped_column(Numeric(18, 4), nullable=True)
    tempo_tarifado_seg: Mapped[int] = mapped_column(Integer, nullable=True)
    custo_total: Mapped[float] = mapped_column(Numeric(18, 4), nullable=True)
    faturamento: Mapped[float] = mapped_column(Numeric(18, 4), nullable=True)
    lucro: Mapped[float] = mapped_column(Numeric(18, 4), nullable=True)
    margem: Mapped[float] = mapped_column(Numeric(18, 4), nullable=True)
    markup: Mapped[float] = mapped_column(Numeric(18, 4), nullable=True)
    periodo_consulta: Mapped[str] = mapped_column(String(80), nullable=True)
    data_coleta: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    dia_consulta: Mapped[date] = mapped_column(Date(), nullable=True)
    gateway_id: Mapped[int] = mapped_column(Integer, nullable=True)
    gateway_name: Mapped[str] = mapped_column(String(150), nullable=True)
    data_operacao: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    tipo_operacao: Mapped[str] = mapped_column(String(120), nullable=True)
    descricao: Mapped[str] = mapped_column(String(512), nullable=True)
    valor: Mapped[float] = mapped_column(Numeric(18, 4), nullable=True)
    saldo_anterior: Mapped[float] = mapped_column(Numeric(18, 4), nullable=True)
    saldo_posterior: Mapped[float] = mapped_column(Numeric(18, 4), nullable=True)


class TodosAssinantes(FinancialMixin, Base):
    __tablename__ = "todos_assinantes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)


class TodosAssinantesHist(FinancialMixin, Base):
    __tablename__ = "todos_assinantes_hist"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)


class RelatorioAssinantesDiario(FinancialMixin, Base):
    __tablename__ = "relatorio_assinantes_diario"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)


class RelatorioAssinantesSemanal(FinancialMixin, Base):
    __tablename__ = "relatorio_assinantes_semanal"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)


class RelatorioAssinantesQuinzenal(FinancialMixin, Base):
    __tablename__ = "relatorio_assinantes_quinzenal"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)


class RelatorioAssinantesMensal(FinancialMixin, Base):
    __tablename__ = "relatorio_assinantes_mensal"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)


class RelatorioAssinantesPorPeriodo(FinancialMixin, Base):
    __tablename__ = "relatorio_assinantes_por_periodo"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)


class RelatorioRotasDiario(FinancialMixin, Base):
    __tablename__ = "relatorio_rotas_diario"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)


class HistoricoSaldosDiario(FinancialMixin, Base):
    __tablename__ = "historico_saldos_diario"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)


class MargemLucroOperacional(FinancialMixin, Base):
    __tablename__ = "margem_lucro_operacional"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)


class SipcodesAgregado(FinancialMixin, Base):
    __tablename__ = "sipcodes_agregado"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)


class VariacoesAssinantes(FinancialMixin, Base):
    __tablename__ = "variacoes_assinantes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)


class VwPriorizeHist(FinancialMixin, Base):
    __tablename__ = "vw_priorize_hist"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
