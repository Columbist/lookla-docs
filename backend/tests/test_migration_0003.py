"""
T-003: address_district backfill — tests written BEFORE migration code.

All tests are static (no DB connection). They verify:
- mapping correctness and completeness
- migration SQL safety (idempotency, no DDL, no overwrite)
"""
import importlib.util
import inspect
from pathlib import Path

MIGRATION_FILE = (
    Path(__file__).parent.parent / "alembic" / "versions" / "0003_backfill_address_district.py"
)
MAPPING_FILE = Path(__file__).parent.parent / "app" / "data" / "district_mapping.py"


def _load_migration():
    spec = importlib.util.spec_from_file_location("migration_0003", MIGRATION_FILE)
    assert spec is not None
    assert spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


# ── Mapping tests ─────────────────────────────────────────────────────────────

def test_mapping_file_exists():
    assert MAPPING_FILE.exists(), "district_mapping.py must exist before migration"


def test_mapping_covers_major_athens_districts():
    from app.data.district_mapping import CITY_TO_DISTRICT
    required_districts = {
        "Glyfada", "Kifissia", "Marousi", "Piraeus",
        "Chalandri", "Nea Smyrni", "Kallithea",
        "Athens Center", "Peristeri",
    }
    actual_districts = set(CITY_TO_DISTRICT.values())
    missing = required_districts - actual_districts
    assert not missing, f"Mapping missing required Athens districts: {missing}"


def test_mapping_keys_are_lowercase():
    from app.data.district_mapping import CITY_TO_DISTRICT
    for key in CITY_TO_DISTRICT:
        assert key == key.lower(), f"Mapping key must be lowercase: '{key}'"


def test_mapping_excludes_non_athens_cities():
    from app.data.district_mapping import CITY_TO_DISTRICT
    non_athens = {"θεσσαλονίκη", "πάτρα", "λάρισα", "ηράκλειο κρήτης", "βόλος"}
    overlap = non_athens & set(CITY_TO_DISTRICT.keys())
    assert not overlap, f"Non-Athens cities must not be in mapping: {overlap}"


def test_city_to_district_function_known_city():
    from app.data.district_mapping import city_to_district
    assert city_to_district("Γλυφάδα") == "Glyfada"
    assert city_to_district("γλυφάδα") == "Glyfada"
    assert city_to_district("  Γλυφάδα  ") == "Glyfada"


def test_city_to_district_function_unknown_city():
    from app.data.district_mapping import city_to_district
    assert city_to_district("Θεσσαλονίκη") is None
    assert city_to_district("London") is None
    assert city_to_district("") is None


# ── Migration safety tests ────────────────────────────────────────────────────

def test_migration_file_exists():
    assert MIGRATION_FILE.exists()


def test_revision_chain():
    mod = _load_migration()
    assert mod.revision == "0003"
    assert mod.down_revision == "0002"


def test_no_ddl_operations():
    src = inspect.getsource(_load_migration().upgrade)
    forbidden = ["add_column", "drop_column", "create_table", "drop_table",
                 "create_index", "drop_index", "alter_column"]
    for op_name in forbidden:
        assert op_name not in src, f"Data migration must not call op.{op_name}()"


def test_upgrade_is_idempotent_by_null_guard():
    """upgrade() SQL must filter WHERE address_district IS NULL."""
    src = inspect.getsource(_load_migration().upgrade)
    assert "IS NULL" in src, "Idempotency requires WHERE address_district IS NULL"


def test_upgrade_does_not_overwrite_existing():
    """Same check: IS NULL guard ensures existing values are preserved."""
    src = inspect.getsource(_load_migration().upgrade)
    # No unconditional UPDATE (would overwrite everything)
    assert "IS NULL" in src


def test_downgrade_sets_to_null():
    src = inspect.getsource(_load_migration().downgrade)
    assert "NULL" in src


def test_only_one_head():
    from alembic.config import Config
    from alembic.script import ScriptDirectory
    cfg = Config(str(Path(__file__).parent.parent / "alembic.ini"))
    script = ScriptDirectory.from_config(cfg)
    assert len(script.get_heads()) == 1
