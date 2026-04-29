import builtins
import importlib.util
from pathlib import Path

SCRIPT_PATH = Path(__file__).resolve().parents[1] / "tools" / "import_financial_from_apidb_import.py"
SPEC = importlib.util.spec_from_file_location("import_financial_from_apidb_import", SCRIPT_PATH)
importer = importlib.util.module_from_spec(SPEC)
if SPEC and SPEC.loader:
    SPEC.loader.exec_module(importer)


def test_allowed_tables_do_not_include_usuarios() -> None:
    assert "usuarios" not in importer.ALLOWED_TABLES
    assert all(table.startswith("todos_") or table.startswith("relatorio_") or table.startswith("historico_") or table.startswith("margem_") or table.startswith("sipcodes_") or table.startswith("variacoes_") or table.startswith("vw_") for table in importer.ALLOWED_TABLES)


def test_build_source_database_url_changes_database_name() -> None:
    target = "mysql+pymysql://user:pass@localhost:3317/gerax_manager?charset=utf8mb4"
    source = importer.build_source_database_url(target, "apidb_import")
    assert "apidb_import" in source
    assert "gerax_manager" not in source
    assert source.startswith("mysql+pymysql://user:pass@localhost:3317/")
    assert "charset=utf8mb4" in source


def test_parse_args_dry_run() -> None:
    args = importer.parse_args(["--dry-run"])
    assert args.dry_run is True
    assert args.truncate_target is False
    assert args.confirm_truncate is False


def test_main_requires_confirm_truncate_when_truncate_target(monkeypatch) -> None:
    fake_settings = type("FakeSettings", (), {"database_url": "mysql+pymysql://user:pass@localhost:3317/gerax_manager?charset=utf8mb4"})
    monkeypatch.setattr(importer, "settings", fake_settings)
    result = importer.main(["--truncate-target"])
    assert result == 1


def test_confirm_truncate_accepts_sim_input(monkeypatch) -> None:
    monkeypatch.setattr(builtins, "input", lambda prompt="": "sim")
    assert importer.confirm_truncate(True) is True


def test_confirm_truncate_rejects_default(monkeypatch) -> None:
    monkeypatch.setattr(builtins, "input", lambda prompt="": "")
    assert importer.confirm_truncate(True) is False
