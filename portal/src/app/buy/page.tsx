// src/app/buy/page.tsx
'use client';

import { useState } from 'react';

export default function BuyPage() {
  const [method, setMethod] = useState<'card' | 'crypto'>('card');
  const [email, setEmail] = useState('');
  const [name, setName] = useState('');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<any>(null);

  async function handleCheckout(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    
    try {
      // First register account
      const registerRes = await fetch('/api/auth/register', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password: crypto.randomUUID().slice(0, 12), name }),
      });
      
      const registerData = await registerRes.json();
      
      if (!registerRes.ok) {
        // Account might exist - try login
        setResult({ error: registerData.error || 'Account may exist. Please log in first.' });
        return;
      }
      
      // Then create checkout session
      const checkoutRes = await fetch('/api/checkout', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          method: method === 'card' ? 'stripe' : 'crypto',
          amount: 129,
          currency: 'USD'
        }),
      });
      
      const checkoutData = await checkoutRes.json();
      setResult(checkoutData);
    } catch (e: any) {
      setResult({ error: e.message });
    } finally {
      setLoading(false);
    }
  }

  if (result?.success) {
    return (
      <div className="min-h-screen bg-gray-950 flex items-center justify-center px-4">
        <div className="text-center">
          <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-green-500/10 border border-green-500/20 mb-6">
            <svg className="w-8 h-8 text-green-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
            </svg>
          </div>
          <h1 className="text-2xl font-bold text-white mb-2">Payment Complete!</h1>
          <p className="text-gray-400 mb-6">Your LocalMind license is active.</p>
          <div className="bg-gray-800 rounded-lg p-4 mb-6 inline-block">
            <p className="text-sm text-gray-400">License Key</p>
            <p className="text-lg font-mono text-blue-400">{result.licenseKey}</p>
          </div>
          <div className="space-x-4">
            <a
              href="/login"
              className="bg-blue-600 hover:bg-blue-700 text-white px-6 py-3 rounded-lg font-medium transition inline-block"
            >
              Log In to Download
            </a>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-950">
      <header className="border-b border-gray-800">
        <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 bg-blue-600 rounded-lg flex items-center justify-center">
              <svg className="w-4 h-4 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
              </svg>
            </div>
            <span className="font-semibold text-white">LocalMind</span>
          </div>
        </div>
      </header>

      <main className="max-w-lg mx-auto px-6 py-12">
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-white mb-2">Get LocalMind</h1>
          <p className="text-gray-400">Your AI. Offline. Private. Fast.</p>
        </div>

        <div className="bg-gray-900 border border-gray-800 rounded-2xl p-8">
          {/* Price */}
          <div className="text-center mb-8">
            <span className="text-4xl font-bold text-white">$129</span>
            <span className="text-gray-500"> / lifetime license</span>
          </div>

          {result?.error && (
            <div className="mb-6 p-4 bg-red-500/10 border border-red-500/20 rounded-lg text-red-400">
              {result.error}
            </div>
          )}

          {/* Payment Method Toggle */}
          <div className="flex mb-6 bg-gray-800 rounded-lg p-1">
            <button
              onClick={() => setMethod('card')}
              className={`flex-1 py-2 rounded-md text-sm font-medium transition flex items-center justify-center gap-2 ${
                method === 'card' ? 'bg-blue-600 text-white' : 'text-gray-400'
              }`}
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 10h18M7 15h1m4 0h1m-7 4h12a3 3 0 003-3V8a3 3 0 00-3-3H6a3 3 0 00-3 3v8a3 3 0 003 3z" />
              </svg>
              Card
            </button>
            <button
              onClick={() => setMethod('crypto')}
              className={`flex-1 py-2 rounded-md text-sm font-medium transition flex items-center justify-center gap-2 ${
                method === 'crypto' ? 'bg-blue-600 text-white' : 'text-gray-400'
              }`}
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              Crypto
            </button>
          </div>

          <form onSubmit={handleCheckout} className="space-y-4">
            <div>
              <label className="block text-sm text-gray-400 mb-1">Name</label>
              <input
                type="text"
                value={name}
                onChange={e => setName(e.target.value)}
                className="w-full bg-gray-800 border border-gray-700 rounded-lg px-4 py-2.5 text-white"
                placeholder="Your name"
              />
            </div>

            <div>
              <label className="block text-sm text-gray-400 mb-1">Email</label>
              <input
                type="email"
                value={email}
                onChange={e => setEmail(e.target.value)}
                className="w-full bg-gray-800 border border-gray-700 rounded-lg px-4 py-2.5 text-white"
                placeholder="you@example.com"
                required
              />
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full bg-blue-600 hover:bg-blue-700 text-white font-semibold py-3 rounded-lg transition disabled:opacity-50"
            >
              {loading ? 'Processing...' : method === 'card' ? 'Pay $129 with Card' : 'Pay $129 with Crypto'}
            </button>
          </form>

          <p className="mt-4 text-xs text-gray-500 text-center">
            Secure payment. Lifetime updates included.
          </p>
        </div>
      </main>
    </div>
  );
}
