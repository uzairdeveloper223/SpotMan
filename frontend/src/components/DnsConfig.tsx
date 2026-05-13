import React, { useState, useEffect } from 'react';

export const DnsConfig: React.FC = () => {
  const [domain, setDomain] = useState('');
  const [config, setConfig] = useState<{ active: boolean, blocked_domains: string[] } | null>(null);

  const fetchConfig = async () => {
    try {
      const token = localStorage.getItem('spotman_token');
      const res = await fetch('http://localhost:8000/api/v1/dns', {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (res.status === 401) {
        localStorage.removeItem('spotman_token');
        window.location.reload();
        return;
      }
      const data = await res.json();
      setConfig(data);
    } catch (e) {
      console.error(e);
    }
  };

  useEffect(() => {
    fetchConfig();
  }, []);

  const handleBlock = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!domain.trim()) return;
    
    try {
      const token = localStorage.getItem('spotman_token');
      await fetch('http://localhost:8000/api/v1/dns/block', {
        method: 'POST',
        headers: { 
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({ domain: domain.trim() })
      });
      setDomain('');
      fetchConfig();
    } catch (e) {
      console.error(e);
    }
  };

  const handleUnblock = async (domainToUnblock: string) => {
    try {
      const token = localStorage.getItem('spotman_token');
      await fetch('http://localhost:8000/api/v1/dns/unblock', {
        method: 'POST',
        headers: { 
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({ domain: domainToUnblock })
      });
      fetchConfig();
    } catch (e) {
      console.error(e);
    }
  };

  return (
    <div className="p-6">
      <h1 className="text-3xl font-bold text-gray-100 mb-6">DNS Sinkhole</h1>
      
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-gray-800 p-6 rounded-lg border border-gray-700 shadow-sm shadow-gray-900/50">
          <h2 className="text-lg font-semibold text-gray-100 mb-4">Add Block Rule</h2>
          <form onSubmit={handleBlock} className="flex gap-4">
            <input 
              type="text" 
              placeholder="example.com" 
              value={domain}
              onChange={(e) => setDomain(e.target.value)}
              className="flex-1 bg-gray-900 border border-gray-700 rounded px-4 py-2 text-gray-200 focus:outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500"
            />
            <button 
              type="submit"
              className="bg-indigo-600 hover:bg-indigo-700 text-white px-6 py-2 rounded font-medium transition-colors shadow-lg shadow-indigo-900/20"
            >
              Block
            </button>
          </form>
        </div>

        <div className="bg-gray-800 p-6 rounded-lg border border-gray-700 shadow-sm shadow-gray-900/50">
          <h2 className="text-lg font-semibold text-gray-100 mb-4 flex items-center justify-between">
            Blocked Domains
            {config?.active && (
              <span className="px-2 py-1 rounded text-xs font-semibold bg-green-500/10 text-green-400 border border-green-500/20">Active</span>
            )}
          </h2>
          
          <div className="space-y-2 max-h-96 overflow-y-auto pr-2">
            {!config || config.blocked_domains.length === 0 ? (
              <p className="text-gray-500 italic">No domains currently blocked.</p>
            ) : (
              config.blocked_domains.map(d => (
                <div key={d} className="flex items-center justify-between bg-gray-900 px-4 py-3 rounded border border-gray-700">
                  <span className="text-gray-300 font-mono text-sm">{d}</span>
                  <button 
                    onClick={() => handleUnblock(d)}
                    className="text-red-400 hover:text-red-300 text-sm font-medium transition-colors"
                  >
                    Remove
                  </button>
                </div>
              ))
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
