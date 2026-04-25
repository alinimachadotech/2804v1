import re

from app.core.settings import settings
from app.schemas.router import RouterOptionOut, RouterOut


def make_slug(name: str, ip: str) -> str:
    base = name.lower().strip()
    base = base.replace("/", "-")
    base = re.sub(r"[^a-z0-9\-]+", "-", base)
    base = re.sub(r"-+", "-", base).strip("-")

    ip_suffix = ip.replace(".", "-")

    return f"{base}-{ip_suffix}"


def list_routers() -> list[RouterOut]:
    routers: list[RouterOut] = []

    for index, router_config in enumerate(settings.routers, start=1):
        routers.append(
            RouterOut(
                id=index,
                name=router_config.name,
                slug=make_slug(router_config.name, router_config.ip),
                ip=router_config.ip,
                base_url=f"https://{router_config.ip}",
                is_active=True,
                verify_tls=False,
            )
        )

    return routers


def list_router_options() -> list[RouterOptionOut]:
    return [
        RouterOptionOut(
            id=router.id,
            label=router.name,
            value=router.slug,
        )
        for router in list_routers()
    ]


def get_router_by_id(router_id: int) -> RouterOut | None:
    for router in list_routers():
        if router.id == router_id:
            return router

    return None


def get_router_by_slug(router_slug: str) -> RouterOut | None:
    for router in list_routers():
        if router.slug == router_slug:
            return router

    return None


def get_router_secret_by_router_id(router_id: int):
    """Busca configuração interna de um router com token/key.
    
    IMPORTANTE: Essa função retorna credenciais. Nunca usar em respostas públicas!
    
    Args:
        router_id: ID do router (1-based index)
        
    Returns:
        RouterSettings com token/key, ou None se não encontrado
    """
    routers = settings.routers
    
    if router_id < 1 or router_id > len(routers):
        return None
    
    return routers[router_id - 1]