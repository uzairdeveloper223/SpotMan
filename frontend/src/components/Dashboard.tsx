import React, { useMemo } from 'react';
import { useWebSocket } from '../hooks/useWebSocket';

export const Dashboard: React.FC = () => {
  const { isConnected, lastMessage } = useWebSocket('ws://localhost:8000/ws');

  const stats = useMemo(() => {
    if (lastMessage?.type === 'status_update') {
      return lastMessage.payload;
    }
    return null;
  }, [lastMessage]);

  const formatBytes = (bytes: number) => {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  return (
    <div className="p-6">
      <h1 className="text-3xl font-bold text-gray-100 mb-6">SpotMan Dashboard</h1>
      
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <div className="bg-gray-800 p-6 rounded-lg border border-gray-700 shadow-sm shadow-gray-900/50">
          <h2 className="text-gray-400 text-sm font-medium uppercase tracking-wider mb-2">Connection Status</h2>
          <div className="flex items-center">
            <span className={`w-3 h-3 rounded-full mr-3 ${isConnected ? 'bg-green-500 shadow-[0_0_8px_rgba(34,197,94,0.6)]' : 'bg-red-500 shadow-[0_0_8px_rgba(239,68,68,0.6)]'}`}></span>
            <span className="text-xl font-semibold text-gray-200">
              {isConnected ? 'Connected' : 'Disconnected'}
            </span>
          </div>
        </div>

        <div className="bg-gray-800 p-6 rounded-lg border border-gray-700 shadow-sm shadow-gray-900/50">
          <h2 className="text-gray-400 text-sm font-medium uppercase tracking-wider mb-2">Connected Devices</h2>
          <span className="text-3xl font-bold text-teal-400">
            {stats?.devices ?? 0}
          </span>
        </div>

        <div className="bg-gray-800 p-6 rounded-lg border border-gray-700 shadow-sm shadow-gray-900/50">
          <h2 className="text-gray-400 text-sm font-medium uppercase tracking-wider mb-2">Total Traffic (RX)</h2>
          <span className="text-3xl font-bold text-indigo-400">
            {formatBytes(stats?.traffic?.rx_bytes ?? 0)}
          </span>
        </div>

        <div className="bg-gray-800 p-6 rounded-lg border border-gray-700 shadow-sm shadow-gray-900/50">
          <h2 className="text-gray-400 text-sm font-medium uppercase tracking-wider mb-2">Total Traffic (TX)</h2>
          <span className="text-3xl font-bold text-purple-400">
             {formatBytes(stats?.traffic?.tx_bytes ?? 0)}
          </span>
        </div>
      </div>

      <div className="mt-8 bg-gray-800 rounded-lg border border-gray-700 overflow-hidden shadow-sm shadow-gray-900/50">
        <div className="px-6 py-4 border-b border-gray-700 flex justify-between items-center">
          <h2 className="text-lg font-semibold text-gray-100">Hotspot Status</h2>
          <div className="flex items-center space-x-3">
            {stats?.hotspot?.active ? (
              <span className="px-3 py-1 rounded-full text-xs font-semibold bg-green-500/10 text-green-400 border border-green-500/20">Active</span>
            ) : (
              <span className="px-3 py-1 rounded-full text-xs font-semibold bg-red-500/10 text-red-400 border border-red-500/20">Inactive</span>
            )}
            
            <button
              onClick={async () => {
                const token = localStorage.getItem('spotman_token');
                if (stats?.hotspot?.active) {
                  await fetch('http://localhost:8000/api/v1/hotspot/stop', { method: 'POST', headers: { 'Authorization': `Bearer ${token}` }});
                } else {
                  await fetch('http://localhost:8000/api/v1/hotspot/start', { method: 'POST', headers: { 'Authorization': `Bearer ${token}` }});
                }
              }}
              className={`px-4 py-1.5 rounded text-sm font-bold transition-colors ${stats?.hotspot?.active ? 'bg-red-600 hover:bg-red-500 text-white shadow-lg shadow-red-900/20' : 'bg-teal-600 hover:bg-teal-500 text-white shadow-lg shadow-teal-900/20'}`}
            >
              {stats?.hotspot?.active ? 'Stop Network' : 'Start Network'}
            </button>
          </div>
        </div>
        <div className="p-6">
          <div className="grid grid-cols-2 gap-4 text-sm">
             <div className="flex flex-col">
               <span className="text-gray-400 mb-1">hostapd</span>
               <span className={stats?.hotspot?.hostapd_active ? 'text-green-400' : 'text-red-400'}>
                 {stats?.hotspot?.hostapd_active ? 'Running' : 'Stopped'}
               </span>
             </div>
             <div className="flex flex-col">
               <span className="text-gray-400 mb-1">dnsmasq</span>
               <span className={stats?.hotspot?.dnsmasq_active ? 'text-green-400' : 'text-red-400'}>
                 {stats?.hotspot?.dnsmasq_active ? 'Running' : 'Stopped'}
               </span>
             </div>
          </div>
        </div>
      </div>
    </div>
  );
};
