from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func, text, or_
from typing import Optional
from datetime import datetime
from zoneinfo import ZoneInfo
import math

ATHENS_TZ = ZoneInfo("Europe/Athens")

from app.core.database import get_db
from app.models.salon import Salon, SalonHour, Photo, Service, Review, SocialLink, SalonCategory, ServiceCategory
from app.schemas.salon import SalonListItem, SalonDetail, PaginatedSalons, PhotoOut

router = APIRouter(prefix="/salons", tags=["salons"])

DAY_NAMES = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]

# Maps multilingual city names to Greek (for address_city filter)
CITY_SYNONYMS: dict[str, str] = {
    # RU
    'афины': 'Αθήνα', 'афина': 'Αθήνα',
    'салоники': 'Θεσσαλονίκη', 'фессалоники': 'Θεσσαλονίκη',
    'пирей': 'Πειραιάς',
    'ираклион': 'Ηράκλειο', 'ираклио': 'Ηράκλειο', 'крит': 'Ηράκλειο',
    'патры': 'Πάτρα', 'патрас': 'Πάτρα',
    'родос': 'Ρόδος',
    'корфу': 'Κέρκυρα',
    'волос': 'Βόλος',
    'лариса': 'Λάρισα', 'ларисса': 'Λάρισα',
    'иоаннина': 'Ιωάννινα', 'яннина': 'Ιωάννινα',
    'кавала': 'Καβάλα',
    'халкида': 'Χαλκίδα', 'эвбея': 'Χαλκίδα',
    'серрес': 'Σέρρες',
    'александруполис': 'Αλεξανδρούπολη',
    'ламия': 'Λαμία',
    'верия': 'Βέροια',
    'козани': 'Κοζάνη',
    'катерини': 'Κατερίνη',
    'кифисья': 'Κηφισιά', 'кифисиа': 'Κηφισιά',
    'глифада': 'Γλυφάδα',
    'маруси': 'Μαρούσι',
    'перистери': 'Περιστέρι',
    'никея': 'Νίκαια',
    'каллифея': 'Καλλιθέα', 'каллитеа': 'Καλλιθέα',
    'агия-парасевки': 'Αγία Παρασκευή',
    'илион': 'Ίλιον',
    # UK
    'афіни': 'Αθήνα',
    'салоніки': 'Θεσσαλονίκη', 'фессалоніки': 'Θεσσαλονίκη',
    'пірей': 'Πειραιάς',
    'іракліон': 'Ηράκλειο',
    'патри': 'Πάτρα',
    'корфу': 'Κέρκυρα',
    'волос': 'Βόλος',
    'лариса': 'Λάρισα',
    'яніна': 'Ιωάννινα',
    'кавала': 'Καβάλα',
    'гліфада': 'Γλυφάδα',
    'маруси': 'Μαρούσι',
    'перістері': 'Περιστέρι',
    'кіфісья': 'Κηφισιά',
    # EN
    'athens': 'Αθήνα',
    'thessaloniki': 'Θεσσαλονίκη', 'thessalonica': 'Θεσσαλονίκη',
    'piraeus': 'Πειραιάς',
    'heraklion': 'Ηράκλειο', 'heraklio': 'Ηράκλειο', 'crete': 'Ηράκλειο',
    'patras': 'Πάτρα',
    'rhodes': 'Ρόδος',
    'corfu': 'Κέρκυρα', 'kerkyra': 'Κέρκυρα',
    'volos': 'Βόλος',
    'larisa': 'Λάρισα', 'larissa': 'Λάρισα',
    'ioannina': 'Ιωάννινα', 'janina': 'Ιωάννινα',
    'kavala': 'Καβάλα',
    'chalkida': 'Χαλκίδα', 'chalkis': 'Χαλκίδα',
    'serres': 'Σέρρες',
    'alexandroupolis': 'Αλεξανδρούπολη',
    'lamia': 'Λαμία',
    'veria': 'Βέροια',
    'kozani': 'Κοζάνη',
    'katerini': 'Κατερίνη',
    'kifissia': 'Κηφισιά', 'kifisia': 'Κηφισιά',
    'glyfada': 'Γλυφάδα',
    'marousi': 'Μαρούσι',
    'peristeri': 'Περιστέρι',
    'nikaia': 'Νίκαια', 'nea smyrni': 'Νέα Σμύρνη',
    'kallithea': 'Καλλιθέα',
    'ilion': 'Ίλιον',
}

# Maps multilingual service terms to English keywords for name search
SERVICE_SYNONYMS: dict[str, str] = {
    # RU — services
    'ногти': 'nail', 'ногтей': 'nail', 'ноготь': 'nail',
    'маникюр': 'manicure', 'педикюр': 'pedicure',
    'гель': 'gel', 'акрил': 'acrylic', 'нейл-арт': 'nail art',
    'волосы': 'hair', 'волос': 'hair', 'прическа': 'hair', 'причёска': 'hair',
    'стрижка': 'hair', 'стрижки': 'hair',
    'окраска': 'color', 'покраска': 'color', 'окрашивание': 'color', 'покрасить': 'color',
    'балаяж': 'balayage', 'мелирование': 'highlight',
    'кератин': 'keratin', 'выпрямление': 'keratin',
    'наращивание': 'extension',
    'парикмахер': 'hair', 'парикмахерская': 'hair', 'салон': 'beauty',
    'брови': 'brow', 'бровей': 'brow', 'микроблейдинг': 'brow',
    'ресницы': 'lash', 'ресниц': 'lash', 'наращивание ресниц': 'lash',
    'макияж': 'makeup', 'визаж': 'makeup', 'визажист': 'makeup',
    'массаж': 'massage', 'массажа': 'massage',
    'спа': 'spa',
    'эпиляция': 'wax', 'шугаринг': 'wax', 'депиляция': 'wax', 'воск': 'wax',
    'барбер': 'barber', 'барбершоп': 'barber', 'бритье': 'barber',
    'тату': 'tattoo', 'татуировка': 'tattoo', 'татуаж': 'tattoo',
    'пирсинг': 'piercing',
    'лазер': 'laser', 'лазерная': 'laser',
    'косметолог': 'facial', 'косметология': 'facial', 'чистка лица': 'facial',
    'уход за лицом': 'facial',
    'красота': 'beauty', 'красоты': 'beauty',
    # UK — services
    'нігті': 'nail', 'нігтів': 'nail', 'ніготь': 'nail',
    'манікюр': 'manicure', 'педикюр': 'pedicure',
    'гель': 'gel', 'акрил': 'acrylic',
    'волосся': 'hair', 'зачіска': 'hair', 'зачісок': 'hair',
    'стрижка': 'hair', 'стрижки': 'hair',
    'фарбування': 'color', 'фарба': 'color',
    'балаяж': 'balayage', 'мелірування': 'highlight',
    'кератин': 'keratin',
    'нарощування': 'extension',
    'перукарня': 'hair', 'перукар': 'hair', 'перукарні': 'hair',
    'брови': 'brow', 'брів': 'brow', 'мікроблейдинг': 'brow',
    'вії': 'lash', 'вій': 'lash',
    'макіяж': 'makeup', 'візаж': 'makeup',
    'масаж': 'massage',
    'спа': 'spa',
    'епіляція': 'wax', 'шугарінг': 'wax', 'депіляція': 'wax',
    'барбер': 'barber', 'барбершоп': 'barber',
    'тату': 'tattoo', 'татуювання': 'tattoo',
    'пірсинг': 'piercing',
    'лазер': 'laser',
    'косметолог': 'facial', 'косметологія': 'facial',
    'краса': 'beauty', 'краси': 'beauty',
    # EN plurals / variants
    'nails': 'nail', 'manicures': 'manicure', 'pedicures': 'pedicure',
    'haircut': 'hair', 'haircuts': 'hair', 'hairdresser': 'hair',
    'hairdressing': 'hair', 'hairstyle': 'hair',
    'eyebrows': 'brow', 'eyelashes': 'lash',
    'waxing': 'wax', 'tattooing': 'tattoo', 'barbershop': 'barber',
    'extensions': 'extension', 'highlights': 'highlight',
}

CATEGORY_KEYWORDS: dict[str, list[str]] = {
    'hair':            ['hair', 'κομμωτ', 'coiffure', 'hairdress', 'hairstyl', 'χτένισμ'],
    'nails':           ['nail', 'νύχι', 'manicure', 'pedicure', 'μανικιούρ', 'πεντικιούρ'],
    'barbershop':      ['barber', 'κουρε', 'ξυρισμ', 'barbershop'],
    'skin':            ['skin', 'facial', 'laser', 'beauty', 'dermato', 'δερμα'],
    'waxing':          ['wax', 'threading', 'depil', 'αποτρίχ'],
    'lashes_brows':    ['lash', 'brow', 'eyelash', 'eyebrow', 'φρύδ', 'βλεφαρ'],
    'makeup':          ['makeup', 'make-up', 'μακιγιάζ', 'visagis'],
    'massage':         ['massage', 'μασάζ', 'wellness', 'therapy', 'θεραπε'],
    'spa':             ['spa', 'wellness', 'relax', 'χαλαρ'],
    'tattoo_piercing': ['tattoo', 'piercing', 'τατουάζ'],
    'hair_cut':        ['haircut', 'hair cut', 'κούρεμ', 'κομμωτ'],
    'hair_color':      ['color', 'colour', 'βαφή', 'βαφ', 'χρωμ'],
    'hair_highlights': ['highlight', 'balayage', 'ombre'],
    'hair_treatment':  ['treatment', 'keratin', 'θεραπε'],
    'hair_styling':    ['styling', 'blowdry', 'blowout', 'χτένισ'],
    'hair_extensions': ['extension'],
    'manicure':        ['manicure', 'μανικιούρ'],
    'pedicure':        ['pedicure', 'πεντικιούρ'],
    'gel_nails':       ['gel', 'nail', 'νύχι'],
    'acrylic_nails':   ['acrylic', 'ακρυλικ', 'nail'],
    'nail_art':        ['nail art', 'nail', 'νύχι'],
}


def _translate_query(q: str) -> tuple[Optional[str], Optional[str]]:
    """
    Translate a multilingual search term.
    Returns (translated_q, city_override).
    If the term is a known city name, returns (None, greek_city).
    If it's a service term, returns (english_term, None).
    Otherwise returns (q, None) unchanged.
    """
    q_lower = q.strip().lower()
    if q_lower in CITY_SYNONYMS:
        return None, CITY_SYNONYMS[q_lower]
    if q_lower in SERVICE_SYNONYMS:
        return SERVICE_SYNONYMS[q_lower], None
    return q, None


def _proxy_url(photo) -> str:
    """Return CDN URL directly if already migrated, else proxy endpoint for lazy migration."""
    if "places.googleapis.com" in photo.url:
        return f"/api/media/photo/{photo.id}"
    return photo.url


def _proxy_url_raw(photo_id: int, url: str) -> str:
    if "places.googleapis.com" in url:
        return f"/api/media/photo/{photo_id}"
    return url


def _primary_photo(salon: Salon) -> Optional[str]:
    if not salon.photos:
        return None
    primary = next((p for p in salon.photos if p.is_primary), None)
    return _proxy_url(primary or salon.photos[0])


def _batch_min_prices(salon_ids: list, db: Session, name_keywords: list | None = None) -> dict:
    """Returns {salon_id: min_price_float}. Optionally filtered by service name keywords."""
    if not salon_ids:
        return {}
    where = "salon_id = ANY(:ids) AND price_from >= 5 AND is_active = TRUE"
    params: dict = {"ids": salon_ids}
    if name_keywords:
        clauses = " OR ".join(f"name ILIKE :kw{i}" for i, _ in enumerate(name_keywords))
        where += f" AND ({clauses})"
        for i, kw in enumerate(name_keywords):
            params[f"kw{i}"] = f"%{kw}%"
    rows = db.execute(text(f"""
        SELECT salon_id, MIN(price_from)::float
        FROM services WHERE {where}
        GROUP BY salon_id
    """), params).fetchall()
    return {r[0]: r[1] for r in rows}


def _batch_open_now(salon_ids: list, db: Session) -> dict:
    """Returns {salon_id: bool} — whether each salon is open right now (Athens time)."""
    if not salon_ids:
        return {}
    now = datetime.now(ATHENS_TZ)
    dow = now.weekday()  # 0=Mon … 6=Sun, matches DB convention
    current = now.time().replace(tzinfo=None)
    rows = db.execute(text("""
        SELECT salon_id, open_time, close_time, is_closed
        FROM salon_hours
        WHERE salon_id = ANY(:ids) AND day_of_week = :dow
    """), {"ids": salon_ids, "dow": dow}).fetchall()
    result = {}
    for r in rows:
        if r.is_closed:
            result[r.salon_id] = False
        elif r.open_time and r.close_time:
            result[r.salon_id] = r.open_time <= current <= r.close_time
    return result


def _batch_primary_photos(salon_ids: list, db: Session) -> dict:
    """Single query for primary photos — eliminates N+1 in list/map endpoints."""
    if not salon_ids:
        return {}
    rows = db.execute(text("""
        SELECT DISTINCT ON (salon_id) salon_id, id, url
        FROM photos
        WHERE salon_id = ANY(:ids)
        ORDER BY salon_id, is_primary DESC, id
    """), {"ids": salon_ids}).fetchall()
    return {row.salon_id: _proxy_url_raw(row.id, row.url) for row in rows}


@router.get("/map")
def map_salons(
    city: Optional[str] = None,
    category: Optional[str] = None,
    q: Optional[str] = None,
    min_rating: Optional[float] = None,
    price_level: Optional[int] = None,
    db: Session = Depends(get_db),
):
    """Lightweight endpoint for map view — returns all matching salons with only map fields."""
    if q:
        translated_q, city_from_q = _translate_query(q)
        if city_from_q and not city:
            city = city_from_q
            q = None
        else:
            q = translated_q

    query = db.query(Salon).filter(Salon.is_active == True, Salon.lat != None, Salon.lng != None)

    if city:
        query = query.filter(Salon.address_city.ilike(f"%{city}%"))
    if q:
        search = f"%{q}%"
        query = query.filter(
            or_(
                Salon.name.ilike(search),
                Salon.address_city.ilike(search),
                Salon.address_street.ilike(search),
                Salon.description.ilike(search),
            )
        )
    if category:
        keywords = CATEGORY_KEYWORDS.get(category, [category])
        kw_filters = []
        for kw in keywords:
            pat = f"%{kw}%"
            kw_filters.append(Salon.name.ilike(pat))
            kw_filters.append(Salon.description.ilike(pat))
        if kw_filters:
            query = query.filter(or_(*kw_filters))
    if min_rating:
        query = query.filter(Salon.rating_google >= min_rating)
    if price_level:
        query = query.filter(Salon.price_level == price_level)

    salons = query.order_by(Salon.rating_google.desc().nullslast()).limit(2000).all()
    s_ids = [s.id for s in salons]
    photo_map = _batch_primary_photos(s_ids, db)
    open_map = _batch_open_now(s_ids, db)
    return [
        {
            "id": s.id,
            "name": s.name,
            "slug": s.slug,
            "lat": float(s.lat),
            "lng": float(s.lng),
            "address_city": s.address_city,
            "phone_primary": s.phone_primary,
            "rating_google": float(s.rating_google) if s.rating_google else None,
            "primary_photo": photo_map.get(s.id),
            "is_open_now": open_map.get(s.id),
        }
        for s in salons
    ]


@router.get("/slugs")
def list_slugs(db: Session = Depends(get_db)):
    rows = db.execute(text("SELECT slug, updated_at FROM salons WHERE slug IS NOT NULL AND slug != '' ORDER BY id")).fetchall()
    return [{"slug": r[0], "updated_at": r[1].isoformat() if r[1] else None} for r in rows]


@router.get("", response_model=PaginatedSalons)
def list_salons(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    city: Optional[str] = None,
    category: Optional[str] = None,
    q: Optional[str] = None,
    min_rating: Optional[float] = None,
    price_level: Optional[int] = None,
    verified_only: bool = False,
    db: Session = Depends(get_db),
):
    # Translate multilingual query terms before searching
    if q:
        translated_q, city_from_q = _translate_query(q)
        if city_from_q and not city:
            city = city_from_q
            q = None
        else:
            q = translated_q

    query = db.query(Salon).filter(Salon.is_active == True)

    if city:
        query = query.filter(Salon.address_city.ilike(f"%{city}%"))
    if q:
        search = f"%{q}%"
        query = query.filter(
            or_(
                Salon.name.ilike(search),
                Salon.address_city.ilike(search),
                Salon.address_street.ilike(search),
                Salon.description.ilike(search),
            )
        )
    if category:
        keywords = CATEGORY_KEYWORDS.get(category, [category])
        kw_filters = []
        for kw in keywords:
            pat = f"%{kw}%"
            kw_filters.append(Salon.name.ilike(pat))
            kw_filters.append(Salon.description.ilike(pat))
        if kw_filters:
            query = query.filter(or_(*kw_filters))
    if min_rating:
        query = query.filter(Salon.rating_google >= min_rating)
    if price_level:
        query = query.filter(Salon.price_level == price_level)
    if verified_only:
        query = query.filter(Salon.is_verified == True)

    total = query.count()
    salons = (
        query.order_by(Salon.rating_google.desc().nullslast(), Salon.rating_count.desc())
        .offset((page - 1) * limit)
        .limit(limit)
        .all()
    )

    salon_ids = [s.id for s in salons]
    photo_map = _batch_primary_photos(salon_ids, db)
    price_map = _batch_min_prices(salon_ids, db, CATEGORY_KEYWORDS.get(category) if category else None)
    open_map = _batch_open_now(salon_ids, db)

    items = []
    for s in salons:
        item = SalonListItem.model_validate(s)
        item.primary_photo = photo_map.get(s.id)
        item.min_price = price_map.get(s.id)
        item.is_open_now = open_map.get(s.id)
        items.append(item)

    return PaginatedSalons(
        items=items,
        total=total,
        page=page,
        limit=limit,
        pages=math.ceil(total / limit) if total else 1,
    )


@router.get("/{salon_id}", response_model=SalonDetail)
def get_salon(salon_id: int | str, db: Session = Depends(get_db)):
    if isinstance(salon_id, str) and not salon_id.isdigit():
        salon = db.query(Salon).filter(Salon.slug == salon_id, Salon.is_active == True).first()
    else:
        salon = db.query(Salon).filter(Salon.id == int(salon_id), Salon.is_active == True).first()

    if not salon:
        raise HTTPException(status_code=404, detail="Salon not found")

    detail = SalonDetail.model_validate(salon)
    detail.primary_photo = _primary_photo(salon)
    detail.review_count = len(salon.reviews)
    # Rewrite Google photo URLs to proxy endpoint for lazy R2 migration
    for photo_out, photo_model in zip(detail.photos, salon.photos):
        photo_out.url = _proxy_url(photo_model)
    sorted_reviews = sorted(
        salon.reviews,
        key=lambda r: (r.source == "google", r.published_at is None),
    )
    detail.reviews = sorted_reviews[:10]
    return detail


@router.get("/{salon_id}/photos", response_model=list[PhotoOut])
def get_photos(salon_id: int, db: Session = Depends(get_db)):
    salon = db.query(Salon).filter(Salon.id == salon_id, Salon.is_active == True).first()
    if not salon:
        raise HTTPException(status_code=404, detail="Salon not found")
    photos = [PhotoOut.model_validate(p) for p in salon.photos]
    for out, model in zip(photos, salon.photos):
        out.url = _proxy_url(model)
    return photos
