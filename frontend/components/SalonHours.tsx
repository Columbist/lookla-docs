import type { SalonHour } from '@/lib/api';

const DAY_EL = ['Δευτ', 'Τρίτ', 'Τετ', 'Πέμπ', 'Παρ', 'Σάβ', 'Κυρ'];
const DAY_EN = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];

export default function SalonHours({ hours, locale }: { hours: SalonHour[]; locale: string }) {
  const names = locale === 'el' ? DAY_EL : DAY_EN;
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
            {h.is_closed ? (locale === 'el' ? 'Κλειστό' : 'Closed') : `${h.open_time} – ${h.close_time}`}
          </span>
        </div>
      ))}
    </div>
  );
}
