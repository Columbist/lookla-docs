'use client';
import { useEffect, useState, useRef } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import Link from 'next/link';

interface Conv { id: number; other_name: string; last_body?: string; last_message_at?: string; client_unread: number; }
interface Msg { id: number; body?: string; attachment_url?: string; message_type: string; proposed_slot?: string; sender_user_id: number; sender_name: string; created_at: string; }

export default function MessagesPage({ params }: { params: { locale: string } }) {
  const locale = (params as any).locale ?? 'el';
  const router = useRouter();
  const sp = useSearchParams();
  const convId = sp ? parseInt(sp.get('conv') || '0') : 0;

  const [me, setMe] = useState<any>(null);
  const [convs, setConvs] = useState<Conv[]>([]);
  const [messages, setMessages] = useState<Msg[]>([]);
  const [newMsg, setNewMsg] = useState('');
  const [loading, setLoading] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);
  const prefix = locale === 'el' ? '' : `/${locale}`;

  useEffect(() => {
    fetch('/api/auth/me', { credentials: 'include' })
      .then(r => r.ok ? r.json() : null)
      .then(d => { if (!d) router.push(`${prefix}/login`); else setMe(d); });
    fetch('/api/chat/conversations', { credentials: 'include' })
      .then(r => r.json()).then(setConvs).catch(() => []);
  }, []);

  useEffect(() => {
    if (!convId) return;
    const load = () => fetch(`/api/chat/conversations/${convId}/messages`, { credentials: 'include' })
      .then(r => r.json()).then(d => { setMessages(d); bottomRef.current?.scrollIntoView(); });
    load();
    const t = setInterval(load, 8000); // poll every 8s
    return () => clearInterval(t);
  }, [convId]);

  const send = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newMsg.trim() || !convId) return;
    setLoading(true);
    await fetch(`/api/chat/conversations/${convId}/messages`, {
      method: 'POST', credentials: 'include',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ body: newMsg }),
    });
    setNewMsg('');
    setLoading(false);
    fetch(`/api/chat/conversations/${convId}/messages`, { credentials: 'include' })
      .then(r => r.json()).then(d => { setMessages(d); setTimeout(() => bottomRef.current?.scrollIntoView(), 100); });
  };

  const selectedConv = convs.find(c => c.id === convId);

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col">
      <header className="bg-white border-b px-4 py-3 flex items-center gap-3">
        <Link href={`${prefix}/account`} className="text-gray-400 hover:text-gray-600">←</Link>
        <Link href={`${prefix}/`} className="text-xl font-bold text-pink-600">Lookla</Link>
        <span className="text-sm text-gray-600">Μηνύματα</span>
      </header>

      <div className="flex-1 flex overflow-hidden max-h-[calc(100vh-57px)]">
        {/* Conversations list */}
        <div className={`w-full md:w-72 bg-white border-r overflow-y-auto flex-shrink-0 ${convId ? 'hidden md:block' : ''}`}>
          <div className="p-3 border-b">
            <h2 className="font-semibold text-sm text-gray-700">Συνομιλίες</h2>
          </div>
          {convs.length === 0 ? (
            <p className="p-4 text-sm text-gray-400">Δεν υπάρχουν συνομιλίες</p>
          ) : convs.map(c => (
            <Link key={c.id} href={`?conv=${c.id}`}
              className={`flex items-start gap-3 p-3 border-b hover:bg-gray-50 transition-colors ${c.id === convId ? 'bg-pink-50 border-l-2 border-l-pink-500' : ''}`}>
              <div className="w-9 h-9 bg-pink-100 rounded-full flex items-center justify-center text-pink-600 font-semibold text-sm flex-shrink-0">
                {(c.other_name || '?')[0].toUpperCase()}
              </div>
              <div className="min-w-0 flex-1">
                <div className="flex items-center justify-between">
                  <p className="text-sm font-medium text-gray-800 truncate">{c.other_name || 'Σαλόνι'}</p>
                  {c.client_unread > 0 && (
                    <span className="bg-pink-600 text-white text-xs rounded-full w-5 h-5 flex items-center justify-center flex-shrink-0">{c.client_unread}</span>
                  )}
                </div>
                {c.last_body && <p className="text-xs text-gray-400 truncate mt-0.5">{c.last_body}</p>}
              </div>
            </Link>
          ))}
        </div>

        {/* Messages area */}
        {convId ? (
          <div className="flex-1 flex flex-col overflow-hidden">
            {/* Header */}
            <div className="bg-white border-b px-4 py-3 flex items-center gap-3">
              <Link href="?" className="md:hidden text-gray-400 hover:text-gray-600">←</Link>
              <div className="w-8 h-8 bg-pink-100 rounded-full flex items-center justify-center text-pink-600 font-semibold text-sm">
                {(selectedConv?.other_name || '?')[0].toUpperCase()}
              </div>
              <span className="font-medium text-sm text-gray-800">{selectedConv?.other_name || 'Συνομιλία'}</span>
            </div>

            {/* Messages */}
            <div className="flex-1 overflow-y-auto p-4 space-y-3">
              {messages.map(msg => {
                const isMe = me && msg.sender_user_id === me.id;
                return (
                  <div key={msg.id} className={`flex ${isMe ? 'justify-end' : 'justify-start'}`}>
                    <div className={`max-w-xs lg:max-w-md px-3 py-2 rounded-2xl text-sm ${isMe ? 'bg-pink-600 text-white rounded-br-none' : 'bg-white text-gray-800 rounded-bl-none shadow-sm'}`}>
                      {msg.body && <p className="leading-relaxed">{msg.body}</p>}
                      {msg.message_type === 'slot_proposal' && msg.proposed_slot && (
                        <div className={`mt-1 text-xs ${isMe ? 'text-pink-200' : 'text-gray-500'}`}>
                          📅 Προτεινόμενο: {new Date(msg.proposed_slot).toLocaleString('el-GR')}
                        </div>
                      )}
                      <p className={`text-xs mt-1 ${isMe ? 'text-pink-200' : 'text-gray-400'}`}>
                        {new Date(msg.created_at).toLocaleTimeString('el-GR', {hour: '2-digit', minute: '2-digit'})}
                      </p>
                    </div>
                  </div>
                );
              })}
              <div ref={bottomRef} />
            </div>

            {/* Input */}
            <form onSubmit={send} className="bg-white border-t px-4 py-3 flex items-center gap-2">
              <input
                type="text" value={newMsg} onChange={e => setNewMsg(e.target.value)}
                placeholder="Γράψτε μήνυμα..."
                className="flex-1 px-4 py-2 border border-gray-200 rounded-full text-sm focus:outline-none focus:ring-2 focus:ring-pink-200"
              />
              <button type="submit" disabled={loading || !newMsg.trim()}
                className="w-9 h-9 bg-pink-600 text-white rounded-full flex items-center justify-center hover:bg-pink-700 disabled:opacity-50 flex-shrink-0">
                ➤
              </button>
            </form>
          </div>
        ) : (
          <div className="flex-1 hidden md:flex items-center justify-center text-gray-400">
            <div className="text-center">
              <p className="text-4xl mb-3">💬</p>
              <p className="text-sm">Επιλέξτε συνομιλία</p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
