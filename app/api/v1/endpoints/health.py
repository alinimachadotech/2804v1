from fastapi import APIRouter

router = APIRouter(tags=["Health"])


@router.get("/")
def home():
    return {"message": "Funcionando"}


@router.get("/ping")
def ping():
    return {"message": "pong"}


@router.get("/health")
def health():
    return {
        "status": "ok",
        "service": "gerax-manager-api",
    }