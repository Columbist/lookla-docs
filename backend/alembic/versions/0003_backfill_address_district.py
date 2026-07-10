"""backfill address_district for Athens metro salons

Revision ID: 0003
Revises: 0002
Create Date: 2026-07-10

DATA MIGRATION ONLY — no schema changes (DDL-free).

Populates address_district for salons whose city name matches the Athens
metropolitan area mapping frozen below.

Safety:
- Idempotent:              Yes — WHERE address_district IS NULL
- Changes schema:          No
- Overwrites existing:     No — only NULL rows are touched
- Uses external services:  No — local mapping only, no API calls
- Rollback strategy:       Irreversible — see downgrade() for explanation

NOTE: The mapping is frozen inside this file intentionally.
Migrations are immutable historical artifacts. The runtime mapping in
app/data/district_mapping.py may evolve; this migration must not.
"""
import logging
from typing import Sequence, Union

from alembic import op
from sqlalchemy import text

log = logging.getLogger(__name__)

revision: str = "0003"
down_revision: Union[str, None] = "0002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# Frozen at migration time. This migration is a self-contained historical artifact.
# Any future changes to the runtime mapping (app/data/district_mapping.py) must NOT
# affect this migration — do not replace this dict with an import.
CITY_TO_DISTRICT_0003: dict[str, str] = {
    # ── Central Athens ────────────────────────────────────────────────────
    "αθήνα": "Athens Center",
    "αθηνα": "Athens Center",

    # ── South Athens (coastal) ────────────────────────────────────────────
    "γλυφάδα": "Glyfada",
    "παλαιό φάληρο": "Palaio Faliro",
    "νέα σμύρνη": "Nea Smyrni",
    "άλιμος": "Alimos",
    "ηλιούπολη": "Ilioupoli",
    "άγιος δημήτριος αττικής": "Agios Dimitrios",
    "άγιος δημήτριος": "Agios Dimitrios",
    "αργυρούπολη": "Argyroupoli",
    "ελληνικό": "Elliniko",
    "ελληνικό-αργυρούπολη": "Elliniko",
    "βούλα": "Voula",
    "βουλιαγμένη": "Vouliagmeni",
    "βάρη": "Vari",
    "καλλιθέα": "Kallithea",

    # ── Piraeus & port area ───────────────────────────────────────────────
    "πειραιάς": "Piraeus",
    "κερατσίνι": "Keratsini",
    "νίκαια": "Nikaia",
    "μοσχάτο": "Moschato",
    "κορυδαλλός": "Korydallos",
    "πέραμα": "Perama",
    "ταύρος": "Tavros",
    "δραπετσώνα": "Drapetsona",

    # ── East Athens ───────────────────────────────────────────────────────
    "βύρωνας": "Vyronas",
    "ζωγράφου": "Zografou",
    "καισαριανή": "Kaisariani",
    "δάφνη αττικής": "Dafni",
    "δάφνη": "Dafni",
    "αγία παρασκευή": "Agia Paraskevi",
    "χολαργός": "Cholargos",
    "χαλάνδρι": "Chalandri",
    "παλλήνη": "Pallini",
    "γέρακας": "Gerakas",
    "ανθούσα": "Anthousa",

    # ── North Athens ──────────────────────────────────────────────────────
    "μαρούσι": "Marousi",
    "κηφισιά": "Kifissia",
    "νέα ερυθραία": "Nea Erythraia",
    "εκάλη": "Ekali",
    "μεταμόρφωση": "Metamorfosi",
    "νέα ιωνία": "Nea Ionia",
    "γαλάτσι": "Galatsi",
    "βριλήσσια": "Vrilissia",
    "πεντέλη": "Penteli",
    "νέο ψυχικό": "Neo Psychiko",
    "ψυχικό": "Psychiko",
    "φιλοθέη": "Filothei",
    "μελίσσια": "Melissia",
    "νέα φιλαδέλφεια": "Nea Filadelfia",

    # ── West Athens ───────────────────────────────────────────────────────
    "περιστέρι": "Peristeri",
    "ίλιον": "Ilion",
    "αιγάλεω": "Aigaleo",
    "χαϊδάρι": "Chaidari",
    "πετρούπολη": "Petroupoli",
    "αγία βαρβάρα": "Agia Varvara",
    "περαμα": "Perama",

    # ── East Attica ───────────────────────────────────────────────────────
    "κορωπί": "Koropi",
    "μαρκόπουλο μεσογαίας": "Markopoulo",
    "μαρκόπουλο": "Markopoulo",
    "παιανία": "Paiania",
    "σπάτα": "Spata",

    # ── West Attica ───────────────────────────────────────────────────────
    "ελευσίνα": "Elefsina",
    "ασπρόπυργος": "Aspropyrgos",
    "μέγαρα": "Megara",
}


def upgrade() -> None:
    bind = op.get_bind()

    preexisting_non_null = bind.execute(
        text("SELECT COUNT(*) FROM salons WHERE address_district IS NOT NULL")
    ).scalar()

    updated = 0
    for city_lower, district in CITY_TO_DISTRICT_0003.items():
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

    active_still_null = bind.execute(
        text("SELECT COUNT(*) FROM salons WHERE is_active = true AND address_district IS NULL")
    ).scalar()

    log.info(
        "[T-003 backfill] Updated: %d | Pre-existing non-null (untouched): %d | Active still NULL: %d",
        updated, preexisting_non_null, active_still_null,
    )


def downgrade() -> None:
    """Irreversible — data backfill cannot be safely undone.

    This migration cannot distinguish values it populated from values that
    existed before the migration or were entered manually afterwards.
    Rolling back by district name would silently delete pre-existing or
    manually-edited data.

    If rollback is required, restore from the pre-migration database backup.
    """
    raise RuntimeError(
        "Migration 0003 is irreversible: address_district values cannot be "
        "safely distinguished from pre-existing or manually-entered data. "
        "Restore from the pre-migration database backup if rollback is needed."
    )
