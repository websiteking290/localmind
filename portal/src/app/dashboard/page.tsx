// src/app/dashboard/page.tsx
'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';

interface User {
  email: string;
  name: string;
  license_key: string;
  is_paid: number;
  purchase_date: string | null;
}

interface Update {
  id: string;
  version: string;
  title: string;
  description: string;
  download_url: string;
  release_date: string;
  downloaded: number;
}

export default function DashboardPage() {
  const [user, setUser] = useState<User | null>(null);
  const [updates, setUpdates] = useState<Update[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const router = useRouter();

  useEffect(() => {
    fetchUserData();
  }, []);

  async function fetchUserData() {
    try {
      const res = await fetch('/api/user');
      if (!res.ok) {
        if (res.status === 401) router.push('/login');
        return;
      }
      const data = await res.json();
      setUser(data.user);
      setUpdates(data.updates || []);
    } catch (e: any) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }

  async function handleLogout() {
    await fetch('/api/auth/logout', { method: 'POST' });
    router.push('/login');
    router.refresh();
  }

  if (loading) return (
    <div className="min-h-screen bg-gray-950 flex items-center justify-center text-gray-400">
      Loading...
    </div>
  );

  return (
    <div className="min-h-screen bg-gray-950">
      {/* Header */}
      <header className="border-b border-gray-800 bg-gray-900/50">
        <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 bg-blue-600 rounded-lg flex items-center justify-center">
              <svg className="w-4 h-4 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
              </svg>
            </div>
            <span className="font-semibold text-white">LocalMind</span>
          </div>
          <div className="flex items-center gap-4">
            <span className="text-sm text-gray-400">{user?.email}</span>
            <button
              onClick={handleLogout}
              className="text-sm text-red-400 hover:text-red-300 transition"
            >
              Log Out
            </button>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-6 py-8">
        {error && (
          <div className="mb-6 p-4 bg-red-500/10 border border-red-500/20 rounded-lg text-red-400">
            {error}
          </div>
        )}

        {/* License Card */}
        <div className="mb-8 bg-gray-900 border border-gray-800 rounded-2xl p-6">
          <div className="flex items-start justify-between">
            <div>
              <h2 className="text-lg font-semibold text-white mb-1">License Status</h2>
              <div className="flex items-center gap-2 mb-2">
                <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                  user?.is_paid 
                    ? 'bg-green-500/10 text-green-400 border border-green-500/20'
                    : 'bg-yellow-500/10 text-yellow-400 border border-yellow-500/20'
                }`}>
                  {user?.is_paid ? 'Active' : 'Trial'}
                </span>
                <span className="text-sm text-gray-400">Purchased: {user?.purchase_date ? new Date(user.purchase_date).toLocaleDateString() : 'N/A'}</span>
              </div>
              <div className="bg-gray-800 rounded-lg px-4 py-2 inline-block">
                <span className="text-xs text-gray-500">License Key: </span>
                <span className="text-sm font-mono text-blue-400">{user?.license_key}</span>
              </div>
            </div>
            <a
              href="https://localmind.ai/download"
              className="bg-blue-600 hover:bg-blue-700 text-white px-6 py-3 rounded-lg font-medium transition inline-flex items-center gap-2"
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
              </svg>
              Download Software
            </a>
          </div>
        </div>

        {/* Updates Section */}
        <div className="bg-gray-900 border border-gray-800 rounded-2xl overflow-hidden">
          <div className="px-6 py-4 border-b border-gray-800 flex items-center justify-between">
            <h2 className="text-lg font-semibold text-white">Available Updates</h2>
            <span className="text-sm text-gray-500">{updates.length} update{updates.length !== 1 ? 's' : ''}</span>
          </div>

          {updates.length === 0 ? (
            <div className="px-6 py-12 text-center text-gray-500">
              No updates available. You're on the latest version.
            </div>
          ) : (
            <div className="divide-y divide-gray-800">
              {updates.map((update) => (
                <div key={update.id} className="px-6 py-5 flex items-center justify-between hover:bg-gray-800/50 transition">
                  <div className="flex-1">
                    <div className="flex items-center gap-3 mb-1">
                      <span className="bg-blue-500/10 text-blue-400 px-2 py-0.5 rounded text-xs font-medium border border-blue-500/20">
                        {update.version}
                      </span>
                      <span className="text-xs text-gray-500">{new Date(update.release_date).toLocaleDateString()}</span>
                      {update.downloaded === 1 && (
                        <span className="text-xs text-green-400">Downloaded</span>
                      )}
                    </div>
                    <h3 className="font-medium text-white mb-1">{update.title}</h3>
                    <p className="text-sm text-gray-400">{update.description}</p>
                  </div>
                  <a
                    href={update.download_url}
                    className={`ml-4 px-4 py-2 rounded-lg text-sm font-medium transition inline-flex items-center gap-2 ${
                      update.downloaded === 1
                        ? 'bg-gray-800 text-gray-400 hover:text-white'
                        : 'bg-blue-600 hover:bg-blue-700 text-white'
                    }`}
                  >
                    {update.downloaded === 1 ? 'Download Again' : 'Download'}
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
                    </svg>
                  </a>
                </div>
              ))}
            </div>
          )}
        </div>
      </main>
    </div>
  );
}
