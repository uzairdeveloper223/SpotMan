import { useState, useEffect } from 'react';
import { Dashboard } from './components/Dashboard';
import { DeviceList } from './components/DeviceList';
import { DnsConfig } from './components/DnsConfig';
import { Login } from './components/Login';
import { Settings } from './components/Settings';

function App() {
  const [activeTab, setActiveTab] = useState<'dashboard' | 'devices' | 'dns' | 'settings'>('dashboard');
  const [token, setToken] = useState<string | null>(localStorage.getItem('spotman_token'));

  useEffect(() => {
    if (token) {
      localStorage.setItem('spotman_token', token);
    } else {
      localStorage.removeItem('spotman_token');
    }
  }, [token]);

  if (!token) {
    return <Login onLogin={setToken} />;
  }

  const handleLogout = () => {
    setToken(null);
  };

  return (
    <div className="min-h-screen bg-gray-900 text-gray-100 font-mono">
      <nav className="bg-gray-800 border-b border-gray-700 px-6 py-4 flex items-center justify-between shadow-md relative z-10">
        <div className="flex items-center space-x-3">
          <img src="/favicon.svg" alt="SpotMan Logo" className="w-8 h-8 drop-shadow-[0_0_8px_rgba(45,212,191,0.5)]" />
          <span className="text-xl font-bold tracking-tight text-white">SpotMan</span>
        </div>
<div className="flex space-x-2">
           <button
             onClick={() => setActiveTab('dashboard')}
             className={`px-4 py-2 rounded-md text-sm font-medium transition-all duration-200 ${activeTab === 'dashboard' ? 'bg-gray-700 text-white shadow-inner' : 'text-gray-400 hover:text-white hover:bg-gray-700/50'}`}
           >
             Dashboard
           </button>
           <button
             onClick={() => setActiveTab('devices')}
             className={`px-4 py-2 rounded-md text-sm font-medium transition-all duration-200 ${activeTab === 'devices' ? 'bg-gray-700 text-white shadow-inner' : 'text-gray-400 hover:text-white hover:bg-gray-700/50'}`}
           >
             Devices
           </button>
           <button
             onClick={() => setActiveTab('dns')}
             className={`px-4 py-2 rounded-md text-sm font-medium transition-all duration-200 ${activeTab === 'dns' ? 'bg-gray-700 text-white shadow-inner' : 'text-gray-400 hover:text-white hover:bg-gray-700/50'}`}
           >
             DNS Sinkhole
           </button>
           <button
             onClick={() => setActiveTab('settings')}
             className={`px-4 py-2 rounded-md text-sm font-medium transition-all duration-200 ${activeTab === 'settings' ? 'bg-gray-700 text-white shadow-inner' : 'text-gray-400 hover:text-white hover:bg-gray-700/50'}`}
           >
             Settings
           </button>
         </div>
      </nav>

<main className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
         {activeTab === 'dashboard' && <Dashboard />}
         {activeTab === 'devices' && <DeviceList />}
         {activeTab === 'dns' && <DnsConfig />}
         {activeTab === 'settings' && <Settings />}
       </main>
    </div>
  );
}

export default App;
