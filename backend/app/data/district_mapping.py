"""
Athens metropolitan area: Greek city name → English district name.

Keys: lowercase, stripped Greek city names as stored in salons.address_city.
Values: canonical English district name for salons.address_district.

Scope: Athens metro only (DEC-012). Cities outside Attica are intentionally
absent — their address_district stays NULL until national expansion.

Ambiguous names ("Ηράκλειο" = both Irakleio/Attica and Heraklion/Crete;
"Αμπελόκηποι" = both Athens and Thessaloniki) are excluded to avoid
wrong assignments.
"""

CITY_TO_DISTRICT: dict[str, str] = {
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
    "κηφισιά": "Kifissia",
    "αγία παρασκευή": "Agia Paraskevi",
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


def city_to_district(city_name: str) -> str | None:
    """Return English district for a Greek city name, or None if outside Athens metro."""
    if not city_name:
        return None
    return CITY_TO_DISTRICT.get(city_name.lower().strip())
