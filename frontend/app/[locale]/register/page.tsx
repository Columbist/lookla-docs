'use client';
import { useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';

const T: Record<string, Record<string, string>> = {
  el: { title: 'Εγγραφή', name: 'Ονοματεπώνυμο', password: 'Κωδικός', suggest: 'Προτεινόμενος', save_pass: '💡 Αποθηκεύστε τον κωδικό:', google: 'Εγγραφή με Google', or: 'ή', submit: 'Εγγραφή', loading: 'Φόρτωση...', error: 'Σφάλμα εγγραφής', has_account: 'Έχετε ήδη λογαριασμό;', login: 'Σύνδεση', lang_label: 'Προτιμώμενη γλώσσα' },
  en: { title: 'Sign up', name: 'Full name', password: 'Password', suggest: 'Suggest', save_pass: '💡 Save your password:', google: 'Sign up with Google', or: 'or', submit: 'Create account', loading: 'Loading...', error: 'Registration error', has_account: 'Already have an account?', login: 'Log in', lang_label: 'Preferred language' },
  ru: { title: 'Регистрация', name: 'Имя и фамилия', password: 'Пароль', suggest: 'Сгенерировать', save_pass: '💡 Сохраните пароль:', google: 'Войти через Google', or: 'или', submit: 'Создать аккаунт', loading: 'Загрузка...', error: 'Ошибка регистрации', has_account: 'Уже есть аккаунт?', login: 'Войти', lang_label: 'Язык интерфейса' },
  uk: { title: 'Реєстрація', name: "Ім'я та прізвище", password: 'Пароль', suggest: 'Згенерувати', save_pass: '💡 Збережіть пароль:', google: 'Увійти через Google', or: 'або', submit: 'Створити акаунт', loading: 'Завантаження...', error: 'Помилка реєстрації', has_account: 'Вже є акаунт?', login: 'Увійти', lang_label: 'Мова інтерфейсу' },
};

const LANGS = [
  { code: 'el', label: 'Ελληνικά' },
  { code: 'en', label: 'English' },
  { code: 'ru', label: 'Русский' },
  { code: 'uk', label: 'Українська' },
];

export default function RegisterPage({ params }: { params: { locale: string } }) {
  const locale = (params as any).locale ?? 'el';
  const t = T[locale] || T.en;
  const prefix = locale === 'el' ? '' : `/${locale}`;
  const router = useRouter();

  const [form, setForm] = useState({ email: '', password: '', name: '', preferred_language: locale, website_url: '' });
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [generatedPass, setGeneratedPass] = useState('');

  const generatePassword = async () => {
    const r = await fetch('/api/auth/generate-password', { method: 'POST' }); // FIX: POST not GET
    const d = await r.json();
    setGeneratedPass(d.password);
    setForm(f => ({ ...f, password: d.password }));
  };

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true); setError('');
    const r = await fetch('/api/auth/register', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'include',
      body: JSON.stringify(form),
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
          {/* Honeypot */}
          <input name="website_url" value={form.website_url} onChange={e => setForm(f => ({...f, website_url: e.target.value}))} style={{display:'none'}} tabIndex={-1} autoComplete="off" />

          <input type="text" placeholder={t.name} value={form.name}
            onChange={e => setForm(f => ({...f, name: e.target.value}))}
            className="w-full px-4 py-3 border border-gray-200 rounded-xl text-base focus:outline-none focus:ring-2 focus:ring-pink-200" />

          <input type="email" placeholder="Email" required value={form.email}
            onChange={e => setForm(f => ({...f, email: e.target.value}))}
            className="w-full px-4 py-3 border border-gray-200 rounded-xl text-base focus:outline-none focus:ring-2 focus:ring-pink-200" />

          <div className="relative">
            <input type="text" placeholder={t.password} required value={form.password}
              onChange={e => setForm(f => ({...f, password: e.target.value}))}
              className="w-full px-4 py-3 pr-32 border border-gray-200 rounded-xl text-base focus:outline-none focus:ring-2 focus:ring-pink-200" />
            <button type="button" onClick={generatePassword}
              className="absolute right-2 top-1/2 -translate-y-1/2 text-xs text-pink-600 hover:text-pink-700 font-medium whitespace-nowrap px-2 py-1">
              {t.suggest}
            </button>
          </div>
          {generatedPass && (
            <p className="text-sm text-gray-600 bg-yellow-50 border border-yellow-100 rounded-xl px-3 py-2">
              {t.save_pass} <strong>{generatedPass}</strong>
            </p>
          )}

          <select value={form.preferred_language} onChange={e => setForm(f => ({...f, preferred_language: e.target.value}))}
            className="w-full px-4 py-3 border border-gray-200 rounded-xl text-base text-gray-700 focus:outline-none focus:ring-2 focus:ring-pink-200">
            {LANGS.map(l => <option key={l.code} value={l.code}>{l.label}</option>)}
          </select>

          {error && <p className="text-sm text-red-500 bg-red-50 rounded-xl px-3 py-2">{error}</p>}

          <button type="submit" disabled={loading}
            className="w-full py-3 bg-pink-600 text-white rounded-xl text-base font-semibold hover:bg-pink-700 disabled:opacity-50">
            {loading ? t.loading : t.submit}
          </button>
        </form>

        <p className="mt-4 text-center text-sm text-gray-500">
          {t.has_account} <Link href={`${prefix}/login`} className="text-pink-600 font-medium">{t.login}</Link>
        </p>
      </div>
    </div>
  );
}
