'use client';
import { useState } from 'react';

const REASONS_EL = [
  { value: 'closed', label: 'Το κατάστημα είναι κλειστό' },
  { value: 'wrong_phone', label: 'Λάθος τηλέφωνο' },
  { value: 'wrong_address', label: 'Λάθος διεύθυνση' },
  { value: 'wrong_hours', label: 'Λάθος ώρες' },
  { value: 'duplicate', label: 'Διπλή καταχώρηση' },
  { value: 'inappropriate', label: 'Ακατάλληλο περιεχόμενο' },
  { value: 'other', label: 'Άλλο' },
];

interface Props { salonId: number; locale: string; label: string; }

export default function ReportButton({ salonId, locale, label }: Props) {
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

  if (sent) return <p className="text-xs text-gray-400">Ευχαριστούμε για την αναφορά σας</p>;

  return (
    <>
      <button onClick={() => setOpen(true)} className="text-xs text-gray-400 hover:text-gray-600 underline">
        ⚠️ {label}
      </button>

      {open && (
        <div className="fixed inset-0 bg-black/40 z-50 flex items-end sm:items-center justify-center p-4">
          <div className="bg-white rounded-xl p-5 w-full max-w-sm shadow-xl">
            <h3 className="font-semibold text-gray-800 mb-4">Αναφορά προβλήματος</h3>
            <div className="space-y-2 mb-4">
              {REASONS_EL.map(r => (
                <label key={r.value} className="flex items-center gap-2 text-sm text-gray-700 cursor-pointer">
                  <input type="radio" name="reason" value={r.value} checked={reason === r.value}
                    onChange={() => setReason(r.value)} className="accent-pink-600" />
                  {r.label}
                </label>
              ))}
            </div>
            {reason === 'other' && (
              <textarea value={desc} onChange={e => setDesc(e.target.value)}
                placeholder="Περιγράψτε το πρόβλημα..."
                className="w-full border border-gray-200 rounded-lg p-2 text-sm resize-none h-20 focus:outline-none focus:ring-1 focus:ring-pink-300 mb-3" />
            )}
            <div className="flex gap-2">
              <button onClick={() => setOpen(false)} className="flex-1 py-2 border border-gray-200 rounded-lg text-sm text-gray-600 hover:bg-gray-50">Ακύρωση</button>
              <button onClick={submit} disabled={!reason}
                className="flex-1 py-2 bg-pink-600 text-white rounded-lg text-sm font-medium hover:bg-pink-700 disabled:opacity-50">Υποβολή</button>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
