"""baseline

Revision ID: 0001
Revises:
Create Date: 2026-07-09

This is an intentionally empty baseline revision for an existing production
database. The schema already exists; this revision lets Alembic track future
migrations without trying to create or drop anything.

Workflow:
  # Run once on each environment (production, staging, local):
  alembic stamp head
  alembic current  # should print: 0001 (head)

  # Only after stamping, create new revisions:
  alembic revision --autogenerate -m "add address_district column"
"""
from typing import Sequence, Union
from alembic import op  # noqa: F401
import sqlalchemy as sa  # noqa: F401

revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
