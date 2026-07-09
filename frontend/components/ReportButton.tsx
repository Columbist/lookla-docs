'use client';
import { useState } from 'react';
import { useTranslations } from 'next-intl';

const REASON_KEYS = ['closed', 'wrong_phone', 'wrong_address', 'wrong_hours', 'duplicate', 'inappropriate', 'other'] as const;

interface Props { salonId: number; locale: string; label: string; }

export default function ReportButton({ salonId, locale: _locale, label }: Props) {
  const t = useTranslations('report');
  const [open, setOpen] = useState(false);
  const [reason, setReason] = useState('');
  const [desc, setDesc] = useState('');
  const [sent, setSent] = useState(false);

  const submit = async () => {
    if (!reason) return;
    await fetch('/api/reports', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ salon_id: salonId, reason, description: desc }),
    }).catch(() => null);
    setSent(true);
  };

  if (sent) return <p className="text-xs text-gray-400">{t('thanks')}</p>;

  return (
    <>
      <button onClick={() => setOpen(true)} className="text-xs text-gray-400 hover:text-gray-600 underline">
        ⚠️ {label}
      </button>

      {open && (
        <div className="fixed inset-0 bg-black/40 z-50 flex items-end sm:items-center justify-center p-4">
          <div className="bg-white rounded-xl p-5 w-full max-w-sm shadow-xl">
            <h3 className="font-semibold text-gray-800 mb-4">{t('title')}</h3>
            <div className="space-y-2 mb-4">
              {REASON_KEYS.map(key => (
                <label key={key} className="flex items-center gap-2 text-sm text-gray-700 cursor-pointer">
                  <input type="radio" name="reason" value={key} checked={reason === key}
                    onChange={() => setReason(key)} className="accent-pink-600" />
                  {t(key)}
                </label>
              ))}
            </div>
            {reason === 'other' && (
              <textarea value={desc} onChange={e => setDesc(e.target.value)}
                placeholder={t('other')}
                className="w-full border border-gray-200 rounded-lg p-2 text-sm resize-none h-20 focus:outline-none focus:ring-1 focus:ring-pink-300 mb-3" />
            )}
            <div className="flex gap-2">
              <button onClick={() => setOpen(false)} className="flex-1 py-2 border border-gray-200 rounded-lg text-sm text-gray-600 hover:bg-gray-50">{t('cancel')}</button>
              <button onClick={submit} disabled={!reason}
                className="flex-1 py-2 bg-pink-600 text-white rounded-lg text-sm font-medium hover:bg-pink-700 disabled:opacity-50">{t('submit')}</button>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
