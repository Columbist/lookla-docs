"""
T-001: Alembic baseline — static validation only (no DB connection required).

Tests verify migration file structure without running migrations,
so they pass in CI without a live Postgres instance.
"""
import importlib.util
import inspect
from pathlib import Path

MIGRATION_FILE = Path(__file__).parent.parent / "alembic" / "versions" / "0001_baseline.py"
ENV_FILE = Path(__file__).parent.parent / "alembic" / "env.py"


def _load_migration():
    spec = importlib.util.spec_from_file_location("baseline_migration", MIGRATION_FILE)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_baseline_file_exists():
    assert MIGRATION_FILE.exists(), f"Migration file not found: {MIGRATION_FILE}"


def test_baseline_revision_importable():
    mod = _load_migration()
    assert mod is not None


def test_baseline_revision_id():
    mod = _load_migration()
    assert mod.revision == "0001"


def test_baseline_has_no_parent():
    mod = _load_migration()
    assert mod.down_revision is None


def test_baseline_upgrade_is_noop():
    mod = _load_migration()
    src = inspect.getsource(mod.upgrade)
    assert "op." not in src, "Baseline upgrade() must not call any op.* functions"


def test_baseline_downgrade_is_noop():
    mod = _load_migration()
    src = inspect.getsource(mod.downgrade)
    assert "op." not in src, "Baseline downgrade() must not call any op.* functions"


def test_env_imports_all_model_modules():
    src = ENV_FILE.read_text()
    assert "app.models.salon" in src
    assert "app.models.user" in src
    assert "app.models.professional" in src


def test_env_uses_settings_database_url():
    src = ENV_FILE.read_text()
    assert "settings.database_url" in src
    assert "postgresql://" not in src
