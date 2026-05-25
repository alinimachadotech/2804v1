from tools.cadup_hub.blacklist import (
    final_artificial,
    numero_tem_padrao_spam,
    prefixo_artificial,
)


def test_blacklist_de_finais_artificiais():
    assert final_artificial("0000") is True
    assert final_artificial("1234") is True
    assert final_artificial("1287") is False


def test_blacklist_de_prefixos_exatos():
    assert prefixo_artificial("9999") is True
    assert prefixo_artificial("2020") is False


def test_ddd_11_prefixo_9500_eh_artificial():
    assert prefixo_artificial("9500", ddd="11") is True
    assert prefixo_artificial("95001", ddd="11") is True
    assert prefixo_artificial("95001", ddd="13") is False


def test_numero_tem_padrao_spam_por_prefixo_ou_final():
    assert numero_tem_padrao_spam("+55 11 95001-1287") is True
    assert numero_tem_padrao_spam("+55 13 2020-0000") is True
    assert numero_tem_padrao_spam("+55 13 2020-1287") is False

