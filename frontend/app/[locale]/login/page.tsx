'use client';
import { useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';

const T: Record<string, Record<string, string>> = {
  el: { title: 'Σύνδεση', password: 'Κωδικός', google: 'Σύνδεση με Google', or: 'ή', submit: 'Σύνδεση', loading: 'Φόρτωση...', error: 'Λάθος email ή κωδικός', forgot: 'Ξεχάσατε τον κωδικό;', no_account: 'Δεν έχετε λογαριασμό;', register: 'Εγγραφή' },
  en: { title: 'Log in', password: 'Password', google: 'Continue with Google', or: 'or', submit: 'Log in', loading: 'Loading...', error: 'Wrong email or password', forgot: 'Forgot password?', no_account: "Don't have an account?", register: 'Sign up' },
  ru: { title: 'Вход', password: 'Пароль', google: 'Войти через Google', or: 'или', submit: 'Войти', loading: 'Загрузка...', error: 'Неверный email или пароль', forgot: 'Забыли пароль?', no_account: 'Нет аккаунта?', register: 'Зарегистрироваться' },
  uk: { title: 'Вхід', password: 'Пароль', google: 'Увійти через Google', or: 'або', submit: 'Увійти', loading: 'Завантаження...', error: 'Невірний email або пароль', forgot: 'Забули пароль?', no_account: 'Немає акаунту?', register: 'Зареєструватися' },
};

export default function LoginPage({ params }: { params: { locale: string } }) {
  const locale = (params as any).locale ?? 'el';
  const t = T[locale] || T.en;
  const prefix = locale === 'el' ? '' : `/${locale}`;
  const router = useRouter();

  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true); setError('');
    const r = await fetch('/api/auth/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'include',
      body: JSON.stringify({ email, password }),
    });
    setLoading(false);
    if (r.ok) {
      router.push(`${prefix}/account`);
    } else {
      const d = await r.json().catch(() => ({}));
      setError(d.detail || t.error);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center p-4">
      <div className="w-full max-w-sm bg-white rounded-2xl shadow-sm p-8">
        <Link href={prefix || '/'} className="block text-center text-2xl font-bold text-pink-600 mb-6">Lookla</Link>
        <h1 className="text-xl font-semibold text-gray-800 mb-6 text-center">{t.title}</h1>

        <a href="/api/auth/google/start"
           className="flex items-center justify-center gap-2 w-full py-3 border border-gray-200 rounded-xl text-sm text-gray-700 hover:bg-gray-50 mb-4">
          <img src="https://www.google.com/favicon.ico" className="w-4 h-4" alt="" />
          {t.google}
        </a>

        <div className="flex items-center gap-3 mb-4">
          <div className="flex-1 h-px bg-gray-100" />
          <span className="text-xs text-gray-400">{t.or}</span>
          <div className="flex-1 h-px bg-gray-100" />
        </div>

        <form onSubmit={submit} className="space-y-3">
          <input type="email" value={email} onChange={e => setEmail(e.target.value)}
            placeholder="Email" required autoComplete="email"
            className="w-full px-4 py-3 border border-gray-200 rounded-xl text-base focus:outline-none focus:ring-2 focus:ring-pink-200" />
          <input type="password" value={password} onChange={e => setPassword(e.target.value)}
            placeholder={t.password} required autoComplete="current-password"
            className="w-full px-4 py-3 border border-gray-200 rounded-xl text-base focus:outline-none focus:ring-2 focus:ring-pink-200" />
          {error && <p className="text-sm text-red-500 bg-red-50 rounded-xl px-3 py-2">{error}</p>}
          <button type="submit" disabled={loading}
            className="w-full py-3 bg-pink-600 text-white rounded-xl text-base font-semibold hover:bg-pink-700 disabled:opacity-50">
            {loading ? t.loading : t.submit}
          </button>
        </form>

        <div className="mt-4 text-center space-y-2">
          <Link href={`${prefix}/forgot-password`} className="text-sm text-gray-500 hover:text-pink-600 block">{t.forgot}</Link>
          <p className="text-sm text-gray-500">{t.no_account} <Link href={`${prefix}/register`} className="text-pink-600 font-medium">{t.register}</Link></p>
        </div>
      </div>
    </div>
  );
}
