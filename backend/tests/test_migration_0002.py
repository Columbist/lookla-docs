"""
T-002: address_district migration — static validation (no DB connection required).
"""
import importlib.util
import inspect
from pathlib import Path

from alembic.config import Config
from alembic.script import ScriptDirectory

MIGRATION_FILE = (
    Path(__file__).parent.parent / "alembic" / "versions" / "0002_add_address_district.py"
)


def _load_migration():
    spec = importlib.util.spec_from_file_location("migration_0002", MIGRATION_FILE)
    assert spec is not None
    assert spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_migration_file_exists():
    assert MIGRATION_FILE.exists()


def test_revision_chain():
    mod = _load_migration()
    assert mod.revision == "0002"
    assert mod.down_revision == "0001"


def test_upgrade_adds_address_district():
    src = inspect.getsource(_load_migration().upgrade)
    assert "address_district" in src
    assert "add_column" in src


def test_upgrade_creates_index_with_convention_name():
    src = inspect.getsource(_load_migration().upgrade)
    # ix_ prefix follows SQLAlchemy naming convention (not idx_)
    assert "ix_salons_address_district" in src
    assert "create_index" in src


def test_index_is_not_unique():
    src = inspect.getsource(_load_migration().upgrade)
    assert "unique=False" in src


def test_column_nullable():
    from app.models.salon import Salon
    col = Salon.__table__.columns.get("address_district")
    assert col is not None
    # Nullable until T-003 backfill populates existing rows
    assert col.nullable is True


def test_downgrade_drops_index_before_column():
    src = inspect.getsource(_load_migration().downgrade)
    assert "drop_index" in src
    assert "drop_column" in src
    assert src.index("drop_index") < src.index("drop_column")


def test_upgrade_no_autogenerate_drops():
    src = inspect.getsource(_load_migration().upgrade)
    assert "drop_table" not in src
    assert "drop_column" not in src


def test_only_one_head():
    cfg = Config(str(Path(__file__).parent.parent / "alembic.ini"))
    script = ScriptDirectory.from_config(cfg)
    assert len(script.get_heads()) == 1


def test_address_district_in_salon_model():
    from app.models.salon import Salon
    col = Salon.__table__.columns.get("address_district")
    assert col is not None, "address_district column missing from Salon ORM model"
    assert str(col.type) == "VARCHAR(120)"
