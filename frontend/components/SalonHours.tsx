import type { SalonHour } from '@/lib/api';

const DAY_EL = ['Δευτ', 'Τρίτ', 'Τετ', 'Πέμπ', 'Παρ', 'Σάβ', 'Κυρ'];
const DAY_EN = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];
const DAY_RU = ['Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб', 'Вс'];
const DAY_UK = ['Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб', 'Нд'];
const CLOSED: Record<string, string> = { el: 'Κλειστό', en: 'Closed', ru: 'Закрыто', uk: 'Зачинено' };
const DAY_NAMES: Record<string, string[]> = { el: DAY_EL, en: DAY_EN, ru: DAY_RU, uk: DAY_UK };

export default function SalonHours({ hours, locale }: { hours: SalonHour[]; locale: string }) {
  const names = DAY_NAMES[locale] ?? DAY_EN;
  const today = (new Date().getDay() + 6) % 7; // 0=Mon

  const sorted = [...hours].sort((a, b) => a.day_of_week - b.day_of_week);

  return (
    <div className="space-y-1.5">
      {sorted.map(h => (
        <div key={h.day_of_week}
             className={`flex justify-between text-sm px-2 py-1 rounded-lg ${h.day_of_week === today ? 'bg-pink-50 font-medium' : ''}`}>
          <span className={h.day_of_week === today ? 'text-pink-700' : 'text-gray-600'}>
            {names[h.day_of_week]}
          </span>
          <span className={h.is_closed ? 'text-gray-400' : h.day_of_week === today ? 'text-pink-700' : 'text-gray-800'}>
            {h.is_closed ? (CLOSED[locale] ?? 'Closed') : `${h.open_time} – ${h.close_time}`}
          </span>
        </div>
      ))}
    </div>
  );
}
