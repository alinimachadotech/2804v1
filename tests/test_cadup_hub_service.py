from tools.cadup_hub.models import CadupRange
import csv

import pytest

from tools.cadup_hub.service import CadupGenerationError, CadupService, GeracaoCadupRequest


class FakeRepository:
    def __init__(self):
        self.range = CadupRange(
            operadora="TIM",
            cnpj="00000000000000",
            cn="13",
            prefixo="2020",
            mcdu_ini=1200,
            mcdu_fim=1299,
            cidade="Santos",
            uf="SP",
            tipo="M",
            rn1="123",
        )
        self.ranges = [self.range]
        self.used_numbers = set()
        self.blocked_numbers = set()
        self.blocked_tuples = set()
        self.saved_numbers = []
        self.lotes = []
        self.audit_logs = []
        self.lote_status = {}

    def consultar_numero(self, numero):
        return self.range

    def buscar_ranges(self, empresa=None, ddd=None, tipo=None, uf=None, cidade=None):
        ranges = self.ranges
        if empresa:
            ranges = [item for item in ranges if item.operadora == empresa]
        if ddd:
            ranges = [item for item in ranges if item.cn == str(ddd)]
        if tipo:
            ranges = [item for item in ranges if item.tipo == tipo]
        if uf:
            ranges = [item for item in ranges if item.uf == uf]
        if cidade:
            ranges = [item for item in ranges if item.cidade == cidade]
        return ranges

    def capacidade_por_empresa(self, empresa, tipo=None):
        return {"operadora": empresa, "ranges": 1, "capacidade": self.range.capacidade}

    def ranking_empresas(self, tipo=None, ddd=None):
        return [{"operadora": "TIM", "ranges": 1, "capacidade": self.range.capacidade}]

    def criar_lote(self, *, nome, filtros, quantidade_solicitada, created_by=None):
        lote_id = len(self.lotes) + 1
        self.lotes.append(
            {
                "id": lote_id,
                "nome": nome,
                "filtros": filtros,
                "quantidade_solicitada": quantidade_solicitada,
                "created_by": created_by,
            }
        )
        return lote_id

    def atualizar_lote(self, lote_id, *, status, quantidade_gerada):
        self.lote_status[lote_id] = {"status": status, "quantidade_gerada": quantidade_gerada}

    def numero_ja_gerado(self, numero):
        return numero in self.used_numbers

    def numero_em_blocklist(self, numero, ddd, prefixo, mcdu):
        return numero in self.blocked_numbers or (ddd, prefixo, mcdu) in self.blocked_tuples

    def salvar_numeros_gerados(self, lote_id, numeros):
        self.saved_numbers.extend(numeros)
        self.used_numbers.update(item["numero"] for item in numeros)

    def registrar_audit_log(self, **kwargs):
        self.audit_logs.append(kwargs)

    def consultar_lote(self, lote_id):
        return next((item for item in self.lotes if item["id"] == lote_id), None)


def test_capacidade_simples_de_range():
    range_cadup = CadupRange(
        operadora="TIM",
        cnpj=None,
        cn="13",
        prefixo="2020",
        mcdu_ini=1200,
        mcdu_fim=1299,
        cidade=None,
        uf=None,
        tipo="M",
        rn1=None,
    )

    assert range_cadup.capacidade == 100
    assert range_cadup.contem_mcdu("1234") is True
    assert range_cadup.contem_mcdu("9999") is False


def test_consulta_simulada_sem_banco_real():
    service = CadupService(repository=FakeRepository())

    result = service.consultar_numero("551320201234")

    assert result["valido"] is True
    assert result["ddd"] == "13"
    assert result["prefixo"] == "2020"
    assert result["mcdu"] == "1234"
    assert result["range"].operadora == "TIM"


def test_consulta_invalida_nao_chama_banco():
    service = CadupService(repository=FakeRepository())

    result = service.consultar_numero("123")

    assert result["valido"] is False
    assert "10 ou 11 digitos" in result["motivo"]


def test_capacidade_por_empresa_usa_repository_fake():
    service = CadupService(repository=FakeRepository())

    result = service.capacidade_por_empresa("TIM", tipo="M")

    assert result == {"operadora": "TIM", "ranges": 1, "capacidade": 100}


def test_geracao_respeita_quantidade(tmp_path):
    repo = FakeRepository()
    service = CadupService(repository=repo)
    saida = tmp_path / "lista.csv"

    result = service.gerar_lista(
        GeracaoCadupRequest(
            nome_lote="teste",
            empresa="TIM",
            ddd="13",
            tipo="M",
            quantidade=3,
            saida=str(saida),
            modo="sequencial",
        )
    )

    assert result["quantidade_gerada"] == 3
    assert len(repo.saved_numbers) == 3
    assert repo.lote_status[1] == {"status": "concluido", "quantidade_gerada": 3}
    with saida.open(encoding="utf-8") as csvfile:
        rows = list(csv.reader(csvfile))
    assert rows == [["destino"], ["1320201200"], ["1320201201"], ["1320201202"]]


def test_geracao_respeita_limite_por_faixa(tmp_path):
    repo = FakeRepository()
    repo.ranges = [
        repo.range,
        CadupRange("TIM", None, "13", "2021", 1200, 1299, "Santos", "SP", "M", None),
    ]
    service = CadupService(repository=repo)

    service.gerar_lista(
        GeracaoCadupRequest(
            nome_lote="teste",
            empresa="TIM",
            ddd="13",
            tipo="M",
            quantidade=4,
            limite_por_faixa=2,
            saida=str(tmp_path / "lista.csv"),
            modo="sequencial",
        )
    )

    assert [item["numero"] for item in repo.saved_numbers] == [
        "1320201200",
        "1320201201",
        "1320211200",
        "1320211201",
    ]


def test_geracao_ignora_numero_em_blocklist_do_banco(tmp_path):
    repo = FakeRepository()
    repo.blocked_numbers.add("1320201200")
    service = CadupService(repository=repo)

    service.gerar_lista(
        GeracaoCadupRequest(
            nome_lote="teste",
            quantidade=2,
            saida=str(tmp_path / "lista.csv"),
            modo="sequencial",
        )
    )

    assert [item["numero"] for item in repo.saved_numbers] == ["1320201201", "1320201202"]


def test_geracao_nao_repete_numero_ja_gerado(tmp_path):
    repo = FakeRepository()
    repo.used_numbers.add("1320201200")
    service = CadupService(repository=repo)

    service.gerar_lista(
        GeracaoCadupRequest(
            nome_lote="teste",
            quantidade=2,
            saida=str(tmp_path / "lista.csv"),
            modo="sequencial",
        )
    )

    assert [item["numero"] for item in repo.saved_numbers] == ["1320201201", "1320201202"]


def test_geracao_bloqueia_finais_artificiais(tmp_path):
    repo = FakeRepository()
    repo.ranges = [CadupRange("TIM", None, "13", "2020", 0, 2, "Santos", "SP", "M", None)]
    service = CadupService(repository=repo)

    service.gerar_lista(
        GeracaoCadupRequest(
            nome_lote="teste",
            quantidade=2,
            saida=str(tmp_path / "lista.csv"),
            modo="sequencial",
        )
    )

    assert [item["numero"] for item in repo.saved_numbers] == ["1320200001", "1320200002"]


def test_geracao_bloqueia_prefixos_artificiais(tmp_path):
    repo = FakeRepository()
    repo.ranges = [CadupRange("TIM", None, "11", "9500", 1200, 1299, "Sao Paulo", "SP", "M", None)]
    service = CadupService(repository=repo)

    with pytest.raises(CadupGenerationError, match="capacidade util"):
        service.gerar_lista(
            GeracaoCadupRequest(
                nome_lote="teste",
                quantidade=1,
                saida=str(tmp_path / "lista.csv"),
                modo="sequencial",
            )
        )

    assert repo.saved_numbers == []


def test_geracao_respeita_bloqueio_manual_por_ddd_prefixo(tmp_path):
    repo = FakeRepository()
    service = CadupService(repository=repo)

    with pytest.raises(CadupGenerationError, match="capacidade util"):
        service.gerar_lista(
            GeracaoCadupRequest(
                nome_lote="teste",
                quantidade=1,
                saida=str(tmp_path / "lista.csv"),
                bloquear_prefixos="13=2020",
                modo="sequencial",
            )
        )

    assert repo.saved_numbers == []


def test_geracao_sequencial(tmp_path):
    repo = FakeRepository()
    service = CadupService(repository=repo)

    service.gerar_lista(
        GeracaoCadupRequest(
            nome_lote="teste",
            quantidade=3,
            saida=str(tmp_path / "lista.csv"),
            modo="sequencial",
        )
    )

    assert [item["mcdu"] for item in repo.saved_numbers] == ["1200", "1201", "1202"]


def test_geracao_aleatoria_com_seed(tmp_path):
    repo_a = FakeRepository()
    repo_b = FakeRepository()
    service_a = CadupService(repository=repo_a)
    service_b = CadupService(repository=repo_b)

    request_a = GeracaoCadupRequest(
        nome_lote="teste",
        quantidade=5,
        saida=str(tmp_path / "a.csv"),
        modo="aleatorio",
        seed=42,
    )
    request_b = GeracaoCadupRequest(
        nome_lote="teste",
        quantidade=5,
        saida=str(tmp_path / "b.csv"),
        modo="aleatorio",
        seed=42,
    )

    service_a.gerar_lista(request_a)
    service_b.gerar_lista(request_b)

    assert [item["numero"] for item in repo_a.saved_numbers] == [
        item["numero"] for item in repo_b.saved_numbers
    ]
    assert [item["mcdu"] for item in repo_a.saved_numbers] != ["1200", "1201", "1202", "1203", "1204"]
