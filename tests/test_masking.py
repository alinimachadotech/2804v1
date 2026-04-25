"""Testes para funções de masking."""

from app.utils.masking import mask_secret, mask_url


def test_mask_secret_short():
    """Testa masking de secrets curtos."""
    assert mask_secret("ab") == "***"
    assert mask_secret("") == "***"


def test_mask_secret_medium():
    """Testa masking de secrets médios."""
    result = mask_secret("abcdef")
    assert result.startswith("ab")
    assert result.endswith("ef")
    assert result == "ab****ef"


def test_mask_secret_long():
    """Testa masking de secrets longos."""
    secret = "a" * 32
    result = mask_secret(secret)
    assert result.startswith("aa")
    assert result.endswith("aa")
    assert "***" in result


def test_mask_url_nextrouter_style():
    """Testa masking de URLs do NextRouter."""
    url = "/api/onlineCallsAgreggate/token123/key456"
    result = mask_url(url)
    assert "/****/****" in result
    assert "token123" not in result
    assert "key456" not in result


def test_mask_url_no_credentials():
    """Testa masking de URLs sem credenciais."""
    url = "/api/health"
    result = mask_url(url)
    assert result == url
