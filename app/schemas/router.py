from pydantic import BaseModel


class RouterOut(BaseModel):
    id: int
    name: str
    slug: str
    ip: str
    base_url: str
    is_active: bool = True
    verify_tls: bool = False


class RouterOptionOut(BaseModel):
    id: int
    label: str
    value: str