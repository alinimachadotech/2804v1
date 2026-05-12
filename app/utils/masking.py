def mask_secret(value: str) -> str:
    """Mascara secrets/tokens para logging seguro."""
    if not value or len(value) < 4:
        return "***"

    middle_mask = max(4, len(value) - 4)
    return f"{value[:2]}{'*' * middle_mask}{value[-2:]}"


def mask_url(url: str) -> str:
    """Mascara token/key em URLs NextRouter sem ocultar filtros ou IDs."""
    parts = url.split("/")

    try:
        api_index = parts.index("api")
    except ValueError:
        return url

    # NextRouter usa /api/{endpoint}/{token}/{key}/{resource_id?}.
    if len(parts) > api_index + 3:
        masked_parts = list(parts)
        masked_parts[api_index + 2] = "****"
        masked_parts[api_index + 3] = "****"
        return "/".join(masked_parts)

    return url
