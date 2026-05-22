// src/app/admin/page.tsx
'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';

interface UpdateRecord {
  id: string;
  version: string;
  title: string;
  description: string;
  download_url: string;
  checksum: string;
  release_date: string;
  is_active: number;
  sent_emails: number;
}

interface Stats {
  totalUsers: number;
  paidUsers: number;
  totalUpdates: number;
}

export default function AdminPage() {
  const [updates, setUpdates] = useState<UpdateRecord[]>([]);
  const [stats, setStats] = useState<Stats | null>(null);
  const [showNewForm, setShowNewForm] = useState(false);
  const [formData, setFormData] = useState({
    version: '',
    title: '',
    description: '',
    downloadUrl: '',
    checksum: '',
  });
  const [notifyId, setNotifyId] = useState('');
  const [message, setMessage] = useState('');
  const router = useRouter();

  useEffect(() => {
    fetchData();
  }, []);

  async function fetchData() {
    const res = await fetch('/api/admin/updates');
    const data = await res.json();
    setUpdates(data.updates || []);
    
    const statsRes = await fetch('/api/admin/stats');
    const statsData = await statsRes.json();
    setStats(statsData);
  }

  async function handleCreate(e: React.FormEvent) {
    e.preventDefault();
    const res = await fetch('/api/admin/updates', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(formData),
    });
    if (res.ok) {
      setMessage('Update created! Activate to make it live.');
      setShowNewForm(false);
      fetchData();
    }
  }

  async function handleActivate(id: string) {
    const res = await fetch('/api/admin/activate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ id }),
    });
    if (res.ok) {
      setMessage('Update activated!');
      fetchData();
    }
  }

  async function handleNotify(id: string) {
    const res = await fetch('/api/admin/notify', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ updateId: id }),
    });
    if (res.ok) {
      setMessage('Emails queued for paid users!');
      fetchData();
    }
  }

  return (
    <div className="min-h-screen bg-gray-950">
      <header className="border-b border-gray-800 bg-gray-900/50">
        <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 bg-blue-600 rounded-lg flex items-center justify-center">
              <svg className="w-4 h-4 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
              </svg>
            </div>
            <span className="font-semibold text-white">LocalMind Admin</span>
          </div>
          <a href="/dashboard" className="text-sm text-gray-400 hover:text-white transition">User View</a>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-6 py-8">
        {/* Stats */}
        <div className="grid grid-cols-3 gap-4 mb-8">
          <div className="bg-gray-900 border border-gray-800 rounded-xl p-6">
            <p className="text-sm text-gray-400 mb-1">Total Users</p>
            <p className="text-3xl font-bold text-white">{stats?.totalUsers || 0}</p>
          </div>
          <div className="bg-gray-900 border border-gray-800 rounded-xl p-6">
            <p className="text-sm text-gray-400 mb-1">Paid Users</p>
            <p className="text-3xl font-bold text-green-400">{stats?.paidUsers || 0}</p>
          </div>
          <div className="bg-gray-900 border border-gray-800 rounded-xl p-6">
            <p className="text-sm text-gray-400 mb-1">Total Updates</p>
            <p className="text-3xl font-bold text-blue-400">{stats?.totalUpdates || 0}</p>
          </div>
        </div>

        {message && (
          <div className="mb-6 p-4 bg-green-500/10 border border-green-500/20 rounded-lg text-green-400">
            {message}
          </div>
        )}

        {/* New Update Button */}
        <div className="mb-6">
          <button
            onClick={() => setShowNewForm(!showNewForm)}
            className="bg-blue-600 hover:bg-blue-700 text-white px-6 py-3 rounded-lg font-medium transition"
          >
            {showNewForm ? 'Cancel' : 'Create New Update'}
          </button>
        </div>

        {/* New Update Form */}
        {showNewForm && (
          <form onSubmit={handleCreate} className="mb-8 bg-gray-900 border border-gray-800 rounded-2xl p-6 space-y-4">
            <h3 className="text-lg font-semibold text-white mb-4">Create Update</h3>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm text-gray-400 mb-1">Version</label>
                <input
                  value={formData.version}
                  onChange={e => setFormData({...formData, version: e.target.value})}
                  className="w-full bg-gray-800 border border-gray-700 rounded-lg px-4 py-2 text-white"
                  placeholder="1.1.0"
                  required
                />
              </div>
              <div>
                <label className="block text-sm text-gray-400 mb-1">Title</label>
                <input
                  value={formData.title}
                  onChange={e => setFormData({...formData, title: e.target.value})}
                  className="w-full bg-gray-800 border border-gray-700 rounded-lg px-4 py-2 text-white"
                  placeholder="Performance improvements"
                  required
                />
              </div>
            </div>
            <div>
              <label className="block text-sm text-gray-400 mb-1">Description</label>
              <textarea
                value={formData.description}
                onChange={e => setFormData({...formData, description: e.target.value})}
                className="w-full bg-gray-800 border border-gray-700 rounded-lg px-4 py-2 text-white h-24"
                placeholder="What's new in this update..."
              />
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm text-gray-400 mb-1">Download URL</label>
                <input
                  value={formData.downloadUrl}
                  onChange={e => setFormData({...formData, downloadUrl: e.target.value})}
                  className="w-full bg-gray-800 border border-gray-700 rounded-lg px-4 py-2 text-white"
                  placeholder="https://..."
                  required
                />
              </div>
              <div>
                <label className="block text-sm text-gray-400 mb-1">SHA-256 Checksum</label>
                <input
                  value={formData.checksum}
                  onChange={e => setFormData({...formData, checksum: e.target.value})}
                  className="w-full bg-gray-800 border border-gray-700 rounded-lg px-4 py-2 text-white"
                  placeholder="abc123..."
                />
              </div>
            </div>
            <button type="submit" className="bg-blue-600 hover:bg-blue-700 text-white px-6 py-3 rounded-lg font-medium transition">
              Create Update
            </button>
          </form>
        )}

        {/* Updates Table */}
        <div className="bg-gray-900 border border-gray-800 rounded-2xl overflow-hidden">
          <table className="w-full">
            <thead className="bg-gray-800">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase">Version</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase">Title</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase">Status</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase">Emails Sent</th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-400 uppercase">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-800">
              {updates.map(u => (
                <tr key={u.id} className="hover:bg-gray-800/50">
                  <td className="px-6 py-4 text-sm text-white">{u.version}</td>
                  <td className="px-6 py-4 text-sm text-white">{u.title}</td>
                  <td className="px-6 py-4">
                    <span className={`inline-flex px-2 py-0.5 rounded text-xs font-medium ${
                      u.is_active 
                        ? 'bg-green-500/10 text-green-400 border border-green-500/20'
                        : 'bg-gray-800 text-gray-400'
                    }`}>
                      {u.is_active ? 'Active' : 'Draft'}
                    </span>
                  </td>
                  <td className="px-6 py-4 text-sm text-gray-400">{u.sent_emails}</td>
                  <td className="px-6 py-4 text-right space-x-2">
                    {!u.is_active && (
                      <button
                        onClick={() => handleActivate(u.id)}
                        className="text-sm text-blue-400 hover:text-blue-300"
                      >
                        Activate
                      </button>
                    )}
                    {u.is_active && (
                      <button
                        onClick={() => handleNotify(u.id)}
                        className="text-sm text-green-400 hover:text-green-300"
                      >
                        Notify Users
                      </button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </main>
    </div>
  );
}
