import React, { useState, useEffect } from 'react';

interface Device {
  mac_address: string;
  ip_address: string | null;
  hostname: string | null;
  first_seen: string;
  last_seen: string;
  is_banned: boolean;
  bandwidth_limit_rx: number | null;
  bandwidth_limit_tx: number | null;
  is_connected: boolean;
  total_rx_bytes: number;
  total_tx_bytes: number;
}

const formatBytes = (bytes: number) => {
  if (bytes === 0) return '0 B';
  const k = 1024;
  const sizes = ['B', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
};

export const DeviceList: React.FC = () => {
  const [devices, setDevices] = useState<Device[]>([]);
  const [loading, setLoading] = useState(true);

  const fetchDevices = async () => {
    try {
      const token = localStorage.getItem('spotman_token');
      const res = await fetch('http://localhost:8000/api/v1/devices', {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      if (res.status === 401) {
        localStorage.removeItem('spotman_token');
        window.location.reload();
        return;
      }
      const data = await res.json();
      if (Array.isArray(data)) {
        setDevices(data);
      }
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDevices();
    const interval = setInterval(fetchDevices, 5000);
    return () => clearInterval(interval);
  }, []);

  const toggleBan = async (mac: string, currentlyBanned: boolean) => {
    try {
      const token = localStorage.getItem('spotman_token');
      await fetch(`http://localhost:8000/api/v1/devices/${mac}`, {
        method: 'PATCH',
        headers: { 
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({ is_banned: !currentlyBanned })
      });
      fetchDevices();
    } catch (e) {
      console.error(e);
    }
  };

  return (
    <div className="p-6">
      <h1 className="text-3xl font-bold text-gray-100 mb-6">Connected Devices</h1>
      
      <div className="bg-gray-800 rounded-lg border border-gray-700 overflow-hidden shadow-sm shadow-gray-900/50">
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="bg-gray-900/50 border-b border-gray-700 text-sm tracking-wider text-gray-400 uppercase">
                <th className="p-4 font-medium">Status</th>
                <th className="p-4 font-medium">Device Info</th>
                <th className="p-4 font-medium">Traffic</th>
                <th className="p-4 font-medium">Last Seen</th>
                <th className="p-4 font-medium text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-700">
              {loading && devices.length === 0 ? (
                <tr>
                  <td colSpan={5} className="p-4 text-center text-gray-500">Loading devices...</td>
                </tr>
              ) : devices.length === 0 ? (
                <tr>
                  <td colSpan={5} className="p-4 text-center text-gray-500">No devices found.</td>
                </tr>
              ) : (
                devices.map(device => (
                  <tr key={device.mac_address} className="hover:bg-gray-700/50 transition-colors">
                    <td className="p-4">
                      <div className="flex items-center space-x-2">
                        <div className={`w-2.5 h-2.5 rounded-full ${device.is_connected ? 'bg-green-500 shadow-[0_0_8px_rgba(34,197,94,0.6)]' : 'bg-gray-600'}`}></div>
                        <span className={`text-sm ${device.is_connected ? 'text-green-400' : 'text-gray-500'}`}>
                          {device.is_connected ? 'Active' : 'Offline'}
                        </span>
                      </div>
                    </td>
                    <td className="p-4">
                      <div className="text-gray-200 font-medium">{device.hostname || 'Unknown Device'}</div>
                      <div className="text-sm text-gray-400 font-mono">{device.mac_address}</div>
                      <div className="text-xs text-gray-500 mt-0.5">{device.ip_address || 'No IP assigned'}</div>
                    </td>
                    <td className="p-4">
                      <div className="flex flex-col space-y-1">
                        <div className="flex items-center text-sm text-emerald-400">
                          <svg className="w-4 h-4 mr-1.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 14l-7 7m0 0l-7-7m7 7V3"></path></svg>
                          {formatBytes(device.total_rx_bytes)}
                        </div>
                        <div className="flex items-center text-sm text-sky-400">
                          <svg className="w-4 h-4 mr-1.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 10l7-7m0 0l7 7m-7-7v18"></path></svg>
                          {formatBytes(device.total_tx_bytes)}
                        </div>
                      </div>
                    </td>
                    <td className="p-4 text-gray-400 text-sm">
                      {new Date(device.last_seen).toLocaleString()}
                    </td>
                    <td className="p-4 text-right">
                      <button 
                        onClick={() => toggleBan(device.mac_address, device.is_banned)}
                        className={`px-3 py-1 rounded text-sm font-medium transition-colors ${
                          device.is_banned 
                            ? 'bg-red-500/10 text-red-400 hover:bg-red-500/20 border border-red-500/20' 
                            : 'bg-gray-700 text-gray-300 hover:bg-gray-600 border border-gray-600'
                        }`}
                      >
                        {device.is_banned ? 'Banned' : 'Ban'}
                      </button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
