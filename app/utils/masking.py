import re


def mask_secret(value: str) -> str:
    """Mascara secrets/tokens para logging seguro.
    
    Args:
        value: O valor do secret
        
    Returns:
        String do secret mascarado
    """
    if not value or len(value) < 4:
        return "***"
    
    # Mostrar primeiros 2 e últimos 2, resto fica com asteriscos (mínimo 4)
    middle_mask = max(4, len(value) - 4)
    return f"{value[:2]}{'*' * middle_mask}{value[-2:]}"


def mask_url(url: str) -> str:
    """Mascara URL removendo credenciais para logging seguro.
    
    Args:
        url: URL completa com possíveis credenciais
        
    Returns:
        URL mascarada
    """
    # Padrão: URL com endpoint + /token/key no final (NextRouter style)
    # Procura por URLs com 4+ segmentos terminando em /algo/algo
    # Exemplo: /api/onlineCallsAgreggate/token/key
    # NÃO mascara: /api/health (3 segmentos)
    
    parts = url.split('/')
    # URL começando com / resulta em partes como ['', 'api', 'onlineCallsAgreggate', 'token', 'key']
    # Então ['', 'api', 'health'] = 3 partes, ['', 'api', 'onlineCallsAgreggate', 'token', 'key'] = 5 partes
    
    if len(parts) >= 5:  # pelo menos 5 partes = URL com 4 segmentos reais
        # Mascara apenas os últimos 2 segmentos
        masked_parts = parts[:-2] + ['****', '****']
        return '/'.join(masked_parts)
    
    return url


