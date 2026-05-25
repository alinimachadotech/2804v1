from tools.cadup_hub.normalizacao import (
    extrair_ddd_prefixo_mcdu,
    limpar_numero,
    normalizar_numero_brasil,
)


def test_normaliza_numero_sem_codigo_pais():
    assert normalizar_numero_brasil("1320201234") == "1320201234"


def test_normaliza_numero_com_codigo_pais():
    assert normalizar_numero_brasil("551320201234") == "1320201234"
    assert normalizar_numero_brasil("+55 13 2020-1234") == "1320201234"


def test_normaliza_numero_invalido():
    assert normalizar_numero_brasil("55132020") is None
    assert normalizar_numero_brasil("001") is None


def test_extrai_ddd_prefixo_e_mcdu():
    assert extrair_ddd_prefixo_mcdu("551320201234") == {
        "ddd": "13",
        "prefixo": "2020",
        "mcdu": "1234",
        "numero": "1320201234",
    }


def test_extrai_prefixo_movel_com_11_digitos_nacionais():
    partes = extrair_ddd_prefixo_mcdu("+55 11 95001-1234")

    assert partes["ddd"] == "11"
    assert partes["prefixo"] == "95001"
    assert partes["mcdu"] == "1234"


def test_limpar_numero_remove_formatacao():
    assert limpar_numero("+55 13 2020-1234") == "551320201234"

