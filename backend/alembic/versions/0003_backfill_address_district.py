"""backfill address_district for Athens metro salons

Revision ID: 0003
Revises: 0002
Create Date: 2026-07-10

DATA MIGRATION ONLY — no schema changes (DDL-free).

Populates address_district for salons whose city name matches the Athens
metropolitan area mapping in app/data/district_mapping.py.

Safety:
- Idempotent:              Yes — WHERE address_district IS NULL
- Changes schema:          No
- Overwrites existing:     No — only NULL rows are touched
- Uses external services:  No — local mapping only, no API calls
- Rollback strategy:       downgrade() sets backfilled districts back to NULL
                           (manually-set values outside the mapping are preserved)
"""
import logging
from typing import Sequence, Union

from alembic import op
from sqlalchemy import text

from app.data.district_mapping import CITY_TO_DISTRICT

log = logging.getLogger(__name__)

revision: str = "0003"
down_revision: Union[str, None] = "0002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()

    already_set = bind.execute(
        text("SELECT COUNT(*) FROM salons WHERE address_district IS NOT NULL")
    ).scalar()

    updated = 0
    for city_lower, district in CITY_TO_DISTRICT.items():
        result = bind.execute(
            text("""
                UPDATE salons
                   SET address_district = :district
                 WHERE address_district IS NULL
                   AND LOWER(TRIM(address_city)) = :city
            """),
            {"district": district, "city": city_lower},
        )
        updated += result.rowcount

    unknown = bind.execute(
        text("SELECT COUNT(*) FROM salons WHERE is_active = true AND address_district IS NULL")
    ).scalar()

    log.info(
        "[T-003 backfill] Updated: %d | Already set (skipped): %d | Active with unknown district: %d",
        updated, already_set, unknown,
    )


def downgrade() -> None:
    """Set backfilled districts back to NULL.

    Only values produced by this migration (i.e. values present in
    CITY_TO_DISTRICT.values()) are cleared. Districts set manually
    that don't appear in the mapping are preserved.
    """
    district_values = list(set(CITY_TO_DISTRICT.values()))
    op.get_bind().execute(
        text("UPDATE salons SET address_district = NULL WHERE address_district = ANY(:districts)"),
        {"districts": district_values},
    )
