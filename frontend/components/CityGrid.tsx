import Link from 'next/link';
import type { City } from '@/lib/api';

const SALONS_WORD: Record<string, string> = {
  el: 'σαλόνια', en: 'salons', ru: 'салонов', uk: 'салонів',
};

// Greek city name → translations. Key is always the Greek DB value.
const CITY_NAMES: Record<string, Record<string, string>> = {
  'Αθήνα':        { en: 'Athens',        ru: 'Афины',        uk: 'Афіни' },
  'Θεσσαλονίκη': { en: 'Thessaloniki',   ru: 'Салоники',     uk: 'Салоніки' },
  'Πειραιάς':    { en: 'Piraeus',        ru: 'Пирей',        uk: 'Пірей' },
  'Γλυφάδα':     { en: 'Glyfada',        ru: 'Глифада',      uk: 'Гліфада' },
  'Λάρισα':      { en: 'Larissa',        ru: 'Лариса',       uk: 'Лариса' },
  'Πάτρα':       { en: 'Patras',         ru: 'Патры',        uk: 'Патри' },
  'Μαρούσι':     { en: 'Marousi',        ru: 'Маруси',       uk: 'Марусі' },
  'Κηφισιά':     { en: 'Kifisia',        ru: 'Кифисья',      uk: 'Кіфісья' },
  'Καλαμαριά':   { en: 'Kalamaria',      ru: 'Каламарья',    uk: 'Каламарья' },
  'Ηράκλειο':    { en: 'Heraklion',      ru: 'Ираклион',     uk: 'Іракліон' },
  'Βόλος':       { en: 'Volos',          ru: 'Волос',        uk: 'Волос' },
  'Χανιά':       { en: 'Chania',         ru: 'Ханья',        uk: 'Ханья' },
  'Ρόδος':       { en: 'Rhodes',         ru: 'Родос',        uk: 'Родос' },
  'Ιωάννινα':    { en: 'Ioannina',       ru: 'Янина',        uk: 'Яніна' },
  'Καβάλα':      { en: 'Kavala',         ru: 'Кавала',       uk: 'Кавала' },
  'Νέα Ιωνία':   { en: 'Nea Ionia',      ru: 'Неа Иония',    uk: 'Неа Іонія' },
  'Συκιές':      { en: 'Sykies',         ru: 'Сикьес',       uk: 'Сікьєс' },
  'Νεάπολη':     { en: 'Neapoli',        ru: 'Неаполи',      uk: 'Неаполі' },
  'Βύρωνας':     { en: 'Vyronas',        ru: 'Вирнас',       uk: 'Вирнас' },
  'Εύοσμος':     { en: 'Evosmos',        ru: 'Евосмос',      uk: 'Евосмос' },
  'Περιστέρι':   { en: 'Peristeri',      ru: 'Периcтери',    uk: 'Периcтері' },
  'Νέα Ερυθραία':{ en: 'Nea Erythraia',  ru: 'Неа Эрифрея',  uk: 'Неа Еріфрея' },
  'Βελισσάριος': { en: 'Velissarios',    ru: 'Велисарьос',   uk: 'Велісаріос' },
  'Γάζι':        { en: 'Gazi',           ru: 'Гази',         uk: 'Газі' },
  'Ρίο':         { en: 'Rio',            ru: 'Рио',          uk: 'Ріо' },
  'Ανατολή':     { en: 'Anatoli',        ru: 'Анатоли',      uk: 'Анатолі' },
  'Μενεμένη':    { en: 'Menemeni',       ru: 'Менемени',     uk: 'Менемені' },
};

function getCityName(greekName: string, locale: string): string {
  if (locale === 'el') return greekName;
  return CITY_NAMES[greekName]?.[locale] ?? greekName;
}

export default function CityGrid({ cities, locale }: { cities: City[]; locale: string }) {
  const prefix = locale === 'el' ? '' : `/${locale}`;
  const word = SALONS_WORD[locale] || 'salons';
  return (
    <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6 gap-3">
      {cities.map(city => (
        <Link
          key={city.city}
          href={`${prefix}/search?city=${encodeURIComponent(city.city)}`}
          className="p-4 bg-white rounded-xl border border-gray-100 hover:border-pink-200 hover:shadow-sm transition-all min-h-[64px] flex flex-col justify-center"
        >
          <div className="text-base font-semibold text-gray-800 truncate">{getCityName(city.city, locale)}</div>
          <div className="text-sm text-gray-400 mt-0.5">{city.count} {word}</div>
        </Link>
      ))}
    </div>
  );
}
