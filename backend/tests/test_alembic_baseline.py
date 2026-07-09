"""
T-001: Alembic baseline — static validation (no DB connection required).

All tests either inspect file structure or import app code that doesn't
need a live Postgres instance.
"""
import importlib.util
import inspect
from pathlib import Path

MIGRATION_FILE = Path(__file__).parent.parent / "alembic" / "versions" / "0001_baseline.py"
ENV_FILE = Path(__file__).parent.parent / "alembic" / "env.py"


def _load_migration():
    spec = importlib.util.spec_from_file_location("baseline_migration", MIGRATION_FILE)
    assert spec is not None, f"Could not create spec from {MIGRATION_FILE}"
    assert spec.loader is not None, "spec.loader is None — file may be unreadable"
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_baseline_file_exists():
    assert MIGRATION_FILE.exists(), f"Migration file not found: {MIGRATION_FILE}"


def test_baseline_revision_importable():
    assert _load_migration() is not None


def test_baseline_revision_id():
    assert _load_migration().revision == "0001"


def test_baseline_has_no_parent():
    assert _load_migration().down_revision is None


def test_baseline_upgrade_is_noop():
    src = inspect.getsource(_load_migration().upgrade)
    assert "op." not in src, "Baseline upgrade() must not call any op.* functions"


def test_baseline_downgrade_is_noop():
    src = inspect.getsource(_load_migration().downgrade)
    assert "op." not in src, "Baseline downgrade() must not call any op.* functions"


def test_all_models_registered_in_metadata():
    """app/models/__init__.py must register all tables in Base.metadata."""
    import app.models  # noqa: F401
    from app.core.database import Base

    tables = set(Base.metadata.tables.keys())
    expected = {
        "salons", "salon_hours", "photos", "services", "service_categories",
        "salon_categories", "reviews", "social_links", "staff",
        "users", "email_verifications", "password_resets", "refresh_tokens",
        "professionals", "professional_portfolio",
        "professional_availability", "professional_social_links",
    }
    missing = expected - tables
    assert not missing, f"Tables missing from Base.metadata: {missing}"


def test_settings_has_database_url_property():
    """Settings.database_url must be a @property, not a hardcoded field."""
    from app.core.config import Settings
    assert isinstance(Settings.database_url, property)


def test_env_no_hardcoded_database_url():
    """env.py must not contain a hardcoded connection string."""
    src = ENV_FILE.read_text()
    assert "postgresql://" not in src
    assert "postgresql+psycopg2://" not in src


def test_only_one_head():
    """Migration graph must have exactly one head to prevent branch conflicts."""
    from alembic.config import Config
    from alembic.script import ScriptDirectory

    cfg = Config(str(Path(__file__).parent.parent / "alembic.ini"))
    script = ScriptDirectory.from_config(cfg)
    heads = script.get_heads()
    assert len(heads) == 1, f"Expected 1 head, got {len(heads)}: {heads}"
