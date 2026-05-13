from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class ReadOnlyQueryOut(BaseModel):
    model_config = ConfigDict(extra="allow")

    router_name: str
    customer_id: str | None = None
    start: int = 0
    limit: int = 100
    filters: dict[str, Any] = Field(default_factory=dict)
    data: Any
    cached: bool = False


class ReportTotalsMixin(BaseModel):
    model_config = ConfigDict(extra="allow")

    total_records: Any | None = None
    records: Any | None = None
    total_time: Any | None = None
    total_time_text: Any | None = None
    total_value: Any | None = None
    total_cost_value: Any | None = None
    total_profit: Any | None = None
    total_profit_on_ass: Any | None = None
    total_answered: Any | None = None
    total_not_answered: Any | None = None
    total_calls: Any | None = None


class CdrReportOut(ReadOnlyQueryOut, ReportTotalsMixin):
    pass


class CdrDisconnectionReportOut(ReadOnlyQueryOut, ReportTotalsMixin):
    pass


class SipCodesReportOut(ReadOnlyQueryOut, ReportTotalsMixin):
    pass


class ProfitCustomersReportOut(ReadOnlyQueryOut, ReportTotalsMixin):
    pass


class ProfitGatewaysReportOut(ReadOnlyQueryOut, ReportTotalsMixin):
    pass
