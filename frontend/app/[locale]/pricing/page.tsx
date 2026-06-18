'use client';
import { useEffect, useState } from 'react';
import Link from 'next/link';

interface Plan { id: number; slug: string; name: string; target: string; price_eur: number; features: string[]; trial_days: number; }

const LABELS: Record<string, Record<string, string>> = {
  el: { salons: 'Σαλόνια & Στούντιο', masters: 'Ελεύθεροι Επαγγελματίες', month: '/μήνα', free: 'Δωρεάν', try: 'Ξεκινήστε Δωρεάν', subscribe: 'Εγγραφή', trial: 'ημέρες δωρεάν δοκιμή', popular: 'Δημοφιλές' },
  en: { salons: 'Salons & Studios', masters: 'Independent Professionals', month: '/month', free: 'Free', try: 'Start Free', subscribe: 'Subscribe', trial: 'day free trial', popular: 'Popular' },
  ru: { salons: 'Салоны & Студии', masters: 'Независимые Мастера', month: '/мес', free: 'Бесплатно', try: 'Начать бесплатно', subscribe: 'Подписаться', trial: 'дней бесплатно', popular: 'Популярный' },
};

export default function PricingPage({ params }: { params: { locale: string } }) {
  const locale = (params as any).locale ?? 'el';
  const t = LABELS[locale] || LABELS.en;
  const prefix = locale === 'el' ? '' : `/${locale}`;

  const [plans, setPlans] = useState<Plan[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch('/api/payments/plans')
      .then(r => r.json())
      .then(d => { setPlans(d); setLoading(false); })
      .catch(() => setLoading(false));
  }, []);

  const salonPlans = plans.filter(p => p.target === 'salon');
  const masterPlans = plans.filter(p => p.target === 'professional');

  const subscribe = async (plan: Plan) => {
    if (plan.price_eur === 0) {
      window.location.href = `${prefix}/dashboard`;
      return;
    }
    const r = await fetch(`/api/payments/subscribe?plan_id=${plan.id}`, {
      method: 'POST', credentials: 'include',
    });
    if (r.status === 401) { window.location.href = `${prefix}/login?next=/pricing`; return; }
    const d = await r.json();
    if (d.checkout_url) window.location.href = d.checkout_url;
    else if (d.status === 'ok') window.location.href = `${prefix}/dashboard?subscribed=true`;
  };

  const PlanCard = ({ plan, popular }: { plan: Plan; popular?: boolean }) => (
    <div className={`bg-white rounded-2xl p-6 border ${popular ? 'border-pink-400 shadow-lg ring-1 ring-pink-200' : 'border-gray-100'} relative flex flex-col`}>
      {popular && (
        <span className="absolute -top-3 left-1/2 -translate-x-1/2 bg-pink-600 text-white text-xs px-3 py-1 rounded-full font-medium">{t.popular}</span>
      )}
      <h3 className="font-bold text-gray-800 text-lg">{plan.name}</h3>
      <div className="my-4">
        {plan.price_eur === 0 ? (
          <span className="text-3xl font-bold text-gray-800">{t.free}</span>
        ) : (
          <div>
            <span className="text-3xl font-bold text-gray-800">€{plan.price_eur}</span>
            <span className="text-gray-500 text-sm">{t.month}</span>
          </div>
        )}
        {plan.trial_days > 0 && plan.price_eur > 0 && (
          <p className="text-xs text-green-600 mt-1">✓ {plan.trial_days} {t.trial}</p>
        )}
      </div>
      <ul className="space-y-2 flex-1 mb-6">
        {plan.features.map((f, i) => (
          <li key={i} className="flex items-start gap-2 text-sm text-gray-600">
            <span className="text-green-500 mt-0.5">✓</span>
            <span>{f}</span>
          </li>
        ))}
      </ul>
      <button onClick={() => subscribe(plan)}
        className={`w-full py-2.5 rounded-xl text-sm font-semibold transition-colors ${popular ? 'bg-pink-600 text-white hover:bg-pink-700' : 'border border-pink-200 text-pink-600 hover:bg-pink-50'}`}>
        {plan.price_eur === 0 ? t.try : t.subscribe}
      </button>
    </div>
  );

  if (loading) return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center">
      <div className="text-gray-400">Φόρτωση τιμολογίου...</div>
    </div>
  );

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white border-b px-4 py-3">
        <div className="max-w-5xl mx-auto flex items-center justify-between">
          <Link href={`${prefix}/`} className="text-xl font-bold text-pink-600">Lookla</Link>
          <div className="flex gap-2">
            <Link href={`${prefix}/login`} className="text-sm text-gray-600 hover:text-pink-600 px-3 py-1.5">Σύνδεση</Link>
            <Link href={`${prefix}/register`} className="text-sm bg-pink-600 text-white px-3 py-1.5 rounded-lg">Εγγραφή</Link>
          </div>
        </div>
      </header>

      <div className="max-w-5xl mx-auto px-4 py-12">
        <div className="text-center mb-12">
          <h1 className="text-3xl font-bold text-gray-900 mb-3">Τιμολόγηση</h1>
          <p className="text-gray-500">Ξεκινήστε δωρεάν, αναβαθμίστε όταν θέλετε</p>
        </div>

        {/* Salon plans */}
        {salonPlans.length > 0 && (
          <section className="mb-12">
            <h2 className="text-lg font-semibold text-gray-700 mb-6 text-center">{t.salons}</h2>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
              {salonPlans.map((plan, i) => (
                <PlanCard key={plan.id} plan={plan} popular={i === 1} />
              ))}
            </div>
          </section>
        )}

        {/* Master plans */}
        {masterPlans.length > 0 && (
          <section>
            <h2 className="text-lg font-semibold text-gray-700 mb-6 text-center">{t.masters}</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-5 max-w-2xl mx-auto">
              {masterPlans.map((plan, i) => (
                <PlanCard key={plan.id} plan={plan} popular={i === 1} />
              ))}
            </div>
          </section>
        )}

        {/* FAQ */}
        <div className="mt-16 text-center">
          <p className="text-sm text-gray-500">
            Ερωτήσεις; Επικοινωνήστε μαζί μας στο{' '}
            <a href="mailto:hello@lookla.gr" className="text-pink-600 hover:underline">hello@lookla.gr</a>
          </p>
        </div>
      </div>
    </div>
  );
}
