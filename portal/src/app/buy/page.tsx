// src/app/buy/page.tsx
'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';

export default function BuyPage() {
  const [method, setMethod] = useState<'stripe' | 'crypto'>('stripe');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [name, setName] = useState('');
  const [loading, setLoading] = useState(false);
  const [step, setStep] = useState<'account' | 'payment'>('account');
  const [message, setMessage] = useState('');
  const router = useRouter();

  async function createAccount(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    setMessage('');

    try {
      const res = await fetch('/api/auth/register', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password, name }),
      });

      const data = await res.json();
      if (res.ok) {
        setStep('payment');
      } else {
        setMessage(data.error || 'Failed to create account');
      }
    } catch (e: any) {
      setMessage(e.message);
    } finally {
      setLoading(false);
    }
  }

  async function handlePayment(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    setMessage('');

    try {
      const res = await fetch('/api/checkout', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ method, amount: 129, currency: 'USD' }),
      });

      const data = await res.json();
      if (res.ok) {
        setMessage('Payment successful! Redirecting to dashboard...');
        setTimeout(() => {
          router.push('/dashboard');
        }, 2000);
      } else {
        setMessage(data.error || 'Payment failed');
      }
    } catch (e: any) {
      setMessage(e.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="min-h-screen bg-gray-950 py-12 px-4">
      <div className="max-w-2xl mx-auto">
        {/* Hero */}
        <div className="text-center mb-12">
          <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-blue-600 mb-6">
            <svg className="w-8 h-8 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
            </svg>
          </div>
          <h1 className="text-3xl font-bold text-white mb-2">Get LocalMind</h1>
          <p className="text-gray-400">One-time purchase. Lifetime updates. Offline AI.</p>
        </div>

        {/* Pricing Card */}
        <div className="bg-gray-900 border border-gray-800 rounded-2xl p-8 mb-8">
          <div className="flex items-baseline justify-between mb-6">
            <div>
              <span className="text-4xl font-bold text-white">$129</span>
              <span className="text-gray-400 ml-2">USD</span>
            </div>
            <span className="text-green-400 text-sm font-medium">Lifetime License</span>
          </div>

          <ul className="space-y-3 mb-6">
            {[
              '5 AI models pre-installed (LLaMA, Qwen, Phi-4, Mistral, Gemma)',
              '128GB USB-C (400MB/s NVMe-class)',
              'Works on Windows, macOS, Linux',
              'Zero setup — plug & play',
              'Lifetime free software updates',
              '100% offline — no internet needed',
              'Priority customer support',
            ].map((feature) => (
              <li key={feature} className="flex items-start gap-3">
                <svg className="w-5 h-5 text-green-400 flex-shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                </svg>
                <span className="text-gray-300">{feature}</span>
              </li>
            ))}
          </ul>
        </div>

        {message && (
          <div className={`mb-6 p-4 rounded-lg ${
            message.includes('success') 
              ? 'bg-green-500/10 text-green-400 border border-green-500/20'
              : 'bg-red-500/10 text-red-400 border border-red-500/20'
          }`}>
            {message}
          </div>
        )}

        {/* Step 1: Account */}
        {step === 'account' ? (
          <div className="bg-gray-900 border border-gray-800 rounded-2xl p-8">
            <h2 className="text-lg font-semibold text-white mb-6">Step 1: Create Your Account</h2>
            <form onSubmit={createAccount} className="space-y-4">
              <div>
                <label className="block text-sm text-gray-400 mb-1">Name</label>
                <input
                  type="text"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  className="w-full bg-gray-800 border border-gray-700 rounded-lg px-4 py-2.5 text-white focus:outline-none focus:border-blue-500"
                  placeholder="Your name"
                  required
                />
              </div>
              <div>
                <label className="block text-sm text-gray-400 mb-1">Email</label>
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="w-full bg-gray-800 border border-gray-700 rounded-lg px-4 py-2.5 text-white focus:outline-none focus:border-blue-500"
                  placeholder="you@example.com"
                  required
                />
              </div>
              <div>
                <label className="block text-sm text-gray-400 mb-1">Password</label>
                <input
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="w-full bg-gray-800 border border-gray-700 rounded-lg px-4 py-2.5 text-white focus:outline-none focus:border-blue-500"
                  placeholder="Min 8 characters"
                  required
                  minLength={8}
                />
              </div>
              <button
                type="submit"
                disabled={loading}
                className="w-full bg-blue-600 hover:bg-blue-700 text-white font-semibold py-3 rounded-lg transition disabled:opacity-50"
              >
                {loading ? 'Creating...' : 'Continue to Payment'}
              </button>
            </form>
            <p className="mt-4 text-center text-sm text-gray-500">
              Already have an account? <a href="/login" className="text-blue-400 hover:text-blue-300">Log in</a>
            </p>
          </div>
        ) : (
          /* Step 2: Payment */
          <div className="bg-gray-900 border border-gray-800 rounded-2xl p-8">
            <h2 className="text-lg font-semibold text-white mb-6">Step 2: Payment Method</h2>
            
            <div className="flex gap-4 mb-6">
              <button
                onClick={() => setMethod('stripe')}
                className={`flex-1 py-3 rounded-lg border transition ${
                  method === 'stripe'
                    ? 'bg-blue-600/20 border-blue-500 text-blue-400'
                    : 'bg-gray-800 border-gray-700 text-gray-400 hover:text-white'
                }`}
              >
                <div className="flex items-center justify-center gap-2">
                  <svg className="w-5 h-5" viewBox="0 0 24 24" fill="currentColor">
                    <path d="M13.976 9.15c-2.172-.806-3.356-1.426-3.356-2.409 0-.831.683-1.305 1.901-1.305 2.227 0 4.515.858 6.09 1.631l.89-5.494C18.252.975 15.697 0 12.165 0 9.667 0 7.589.654 6.104 1.872 4.56 3.147 3.757 4.992 3.757 7.218c0 4.039 2.467 5.76 6.476 7.219 2.585.92 3.445 1.574 3.445 2.583 0 .98-.84 1.545-2.354 1.545-1.875 0-4.965-.921-6.99-2.109l-.9 5.555C5.175 22.99 8.385 24 11.714 24c2.641 0 4.843-.624 6.328-1.813 1.664-1.305 2.525-3.236 2.525-5.732 0-4.128-2.524-5.851-6.591-7.305z" />
                  </svg>
                  Credit Card (Visa, Mastercard)
                </div>
              </button>
              <button
                onClick={() => setMethod('crypto')}
                className={`flex-1 py-3 rounded-lg border transition ${
                  method === 'crypto'
                    ? 'bg-blue-600/20 border-blue-500 text-blue-400'
                    : 'bg-gray-800 border-gray-700 text-gray-400 hover:text-white'
                }`}
              >
                <div className="flex items-center justify-center gap-2">
                  <svg className="w-5 h-5" viewBox="0 0 24 24" fill="currentColor">
                    <path d="M23.638 14.904c-1.602 6.43-8.113 10.34-14.542 8.736C2.67 22.05-1.244 15.525.362 9.105 1.962 2.67 8.475-1.243 14.9.358c6.43 1.605 10.342 8.115 8.738 14.546zm-6.35-4.613c.24-1.59-.974-2.45-2.64-3.03l.54-2.153-1.315-.33-.52 2.1c-.347-.087-.7-.167-1.053-.247l.525-2.12-1.32-.33-.54 2.15c-.285-.065-.565-.13-.835-.2l-1.815-.45-.35 1.4s.974.22.955.235c.535.136.63.486.615.766l-.615 2.47c.037.01.085.024.138.047l-.14-.035-.865 3.47c-.065.16-.23.4-.6.31.015.02-.96-.24-.96-.24L8.4 16.19l1.715.43c.32.08.63.165.94.24l-.545 2.2 1.32.33.54-2.16c.36.1.705.19 1.05.27l-.54 2.13 1.32.33.545-2.18c2.24.42 3.93.25 4.64-1.77.57-1.63-.03-2.57-1.22-3.18.87-.2 1.525-.78 1.7-1.97h.01z" />
                  </svg>
                  Cryptocurrency (BTC, ETH, USDC)
                </div>
              </button>
            </div>

            <form onSubmit={handlePayment}>
              {method === 'stripe' ? (
                <div className="bg-gray-800 rounded-lg p-4 mb-6">
                  <p className="text-sm text-gray-400 mb-4">You'll be redirected to Stripe's secure checkout.</p>
                  <div className="flex items-center gap-4">
                    <div className="bg-white rounded px-3 py-1">
                      <svg className="h-6 w-auto" viewBox="0 0 48 16" fill="none">
                        <path d="M18.5 0h4.8v11.2h-4.8V0z" fill="#666" />
                        <path d="M0 7.5C0 5 1.8 3.5 4 3.5c1.6 0 2.6.8 3 1.5l-1.3 1c-.2-.4-.8-.9-1.7-.9-1.2 0-2.2.9-2.2 2.4s1 2.4 2.2 2.4c.9 0 1.5-.5 1.8-1l1.2 1c-.5.7-1.5 1.5-3 1.5-2.3 0-4-1.6-4-3.9z" fill="#666" />
                      </svg>
                    </div>
                    <div className="bg-white rounded px-3 py-1">
                      <svg className="h-6 w-auto" viewBox="0 0 48 16" fill="none">
                        <path d="M0 2.5h4.8v11.2H0V2.5z" fill="#666" />
                      </svg>
                    </div>
                  </div>
                </div>
              ) : (
                <div className="bg-gray-800 rounded-lg p-4 mb-6">
                  <p className="text-sm text-gray-400 mb-4">Pay with Bitcoin, Ethereum, or USDC via Coinbase Commerce.</p>
                  <div className="flex items-center gap-4">
                    <div className="bg-orange-500/20 text-orange-400 px-3 py-1 rounded text-sm font-medium">BTC</div>
                    <div className="bg-blue-500/20 text-blue-400 px-3 py-1 rounded text-sm font-medium">ETH</div>
                    <div className="bg-green-500/20 text-green-400 px-3 py-1 rounded text-sm font-medium">USDC</div>
                  </div>
                </div>
              )}

              <button
                type="submit"
                disabled={loading}
                className="w-full bg-blue-600 hover:bg-blue-700 text-white font-semibold py-4 rounded-lg transition disabled:opacity-50 text-lg"
              >
                {loading ? 'Processing...' : `Pay $129 with ${method === 'stripe' ? 'Card' : 'Crypto'}`}
              </button>
            </form>
          </div>
        )}
      </div>
    </div>
  );
}
