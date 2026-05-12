import { useState, useEffect } from 'react'

interface Device {
  IP: string;
  MAC: string;
  Hostname: string;
  Connected: boolean;
  BytesUp: number;
  BytesDown: number;
}

function App() {
  const [devices, setDevices] = useState<Device[]>([]);
  const [hotspotStatus, setHotspotStatus] = useState<'stopped' | 'starting' | 'running'>('stopped');
  const [ssid, setSsid] = useState('SpotMan_AP');
  const [password, setPassword] = useState('password123');
  const [wan, setWan] = useState('eth0');
  const [lan, setLan] = useState('wlan0');

  useEffect(() => {
    const ws = new WebSocket(`ws://${window.location.hostname}:8080/ws`);
    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      setDevices(data);
    };
    return () => ws.close();
  }, []);

  const startHotspot = async () => {
    setHotspotStatus('starting');
    try {
      const res = await fetch('/api/hotspot/start', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ ssid, password, channel: 6, band: '2.4', interface: lan, wan })
      });
      if (res.ok) setHotspotStatus('running');
      else setHotspotStatus('stopped');
    } catch (e) {
      setHotspotStatus('stopped');
    }
  };

  const stopHotspot = async () => {
    await fetch('/api/hotspot/stop', { method: 'POST' });
    setHotspotStatus('stopped');
  };

  const banClient = async (mac: string) => {
    await fetch('/api/client/ban', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ mac })
    });
  };

  return (
    <div className="min-h-screen bg-gray-900 text-white p-8 w-full">
      <header className="mb-12 flex justify-between items-center">
        <div>
          <h1 className="text-4xl font-bold tracking-tight text-white">SpotMan</h1>
          <p className="text-gray-400 mt-2">ISP-Level Linux Hotspot Control</p>
        </div>
        <div className="flex gap-4">
          {hotspotStatus === 'stopped' ? (
            <button onClick={startHotspot} className="bg-green-600 hover:bg-green-700 px-6 py-2 rounded-lg font-medium transition">Start Hotspot</button>
          ) : (
            <button onClick={stopHotspot} className="bg-red-600 hover:bg-red-700 px-6 py-2 rounded-lg font-medium transition">Stop Hotspot</button>
          )}
        </div>
      </header>

      <main className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        <section className="lg:col-span-2 bg-gray-800 rounded-2xl p-6 border border-gray-700">
          <h2 className="text-xl font-semibold mb-6 flex items-center gap-2">
            <span className={`w-3 h-3 rounded-full ${hotspotStatus === 'running' ? 'bg-green-500 animate-pulse' : 'bg-red-500'}`}></span>
            Connected Devices ({devices.length})
          </h2>
          <div className="overflow-x-auto">
            <table className="w-full text-left">
              <thead>
                <tr className="text-gray-400 border-b border-gray-700">
                  <th className="pb-4 font-medium">Device</th>
                  <th className="pb-4 font-medium">IP Address</th>
                  <th className="pb-4 font-medium">MAC Address</th>
                  <th className="pb-4 font-medium">Data (D/U)</th>
                  <th className="pb-4 font-medium text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-700">
                {devices.length === 0 ? (
                  <tr><td colSpan={5} className="py-8 text-center text-gray-500">No devices connected</td></tr>
                ) : (
                  devices.map((device) => (
                    <tr key={device.MAC} className="group hover:bg-gray-750 transition">
                      <td className="py-4 font-medium">{device.Hostname || 'Unknown'}</td>
                      <td className="py-4 text-gray-300 font-mono text-sm">{device.IP}</td>
                      <td className="py-4 text-gray-300 font-mono text-sm">{device.MAC}</td>
                      <td className="py-4 text-gray-300 text-sm">
                        {Math.round(device.BytesDown / 1024 / 1024)} MB / {Math.round(device.BytesUp / 1024 / 1024)} MB
                      </td>
                      <td className="py-4 text-right">
                        <button onClick={() => banClient(device.MAC)} className="text-red-400 hover:text-red-300 text-sm font-medium">Ban</button>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </section>

        <section className="space-y-8">
          <div className="bg-gray-800 rounded-2xl p-6 border border-gray-700">
            <h2 className="text-xl font-semibold mb-6">Configuration</h2>
            <div className="space-y-4">
              <div>
                <label className="block text-sm text-gray-400 mb-1">SSID</label>
                <input value={ssid} onChange={e => setSsid(e.target.value)} className="w-full bg-gray-900 border border-gray-700 rounded-lg px-4 py-2 focus:ring-2 focus:ring-blue-500 outline-none" />
              </div>
              <div>
                <label className="block text-sm text-gray-400 mb-1">Password</label>
                <input type="password" value={password} onChange={e => setPassword(e.target.value)} className="w-full bg-gray-900 border border-gray-700 rounded-lg px-4 py-2 focus:ring-2 focus:ring-blue-500 outline-none" />
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm text-gray-400 mb-1">WAN (Internet)</label>
                  <input value={wan} onChange={e => setWan(e.target.value)} className="w-full bg-gray-900 border border-gray-700 rounded-lg px-4 py-2 focus:ring-2 focus:ring-blue-500 outline-none" />
                </div>
                <div>
                  <label className="block text-sm text-gray-400 mb-1">LAN (Hotspot)</label>
                  <input value={lan} onChange={e => setLan(e.target.value)} className="w-full bg-gray-900 border border-gray-700 rounded-lg px-4 py-2 focus:ring-2 focus:ring-blue-500 outline-none" />
                </div>
              </div>
            </div>
          </div>

          <div className="bg-gray-800 rounded-2xl p-6 border border-gray-700">
            <h2 className="text-xl font-semibold mb-6">Traffic Stats</h2>
            <div className="grid grid-cols-2 gap-4">
              <div className="bg-gray-900 p-4 rounded-xl border border-gray-700">
                <div className="text-gray-400 text-xs uppercase font-bold">Session Down</div>
                <div className="text-2xl font-bold mt-1">
                  {Math.round(devices.reduce((acc, d) => acc + d.BytesDown, 0) / 1024 / 1024)} MB
                </div>
              </div>
              <div className="bg-gray-900 p-4 rounded-xl border border-gray-700">
                <div className="text-gray-400 text-xs uppercase font-bold">Session Up</div>
                <div className="text-2xl font-bold mt-1">
                  {Math.round(devices.reduce((acc, d) => acc + d.BytesUp, 0) / 1024 / 1024)} MB
                </div>
              </div>
            </div>
          </div>
        </section>
      </main>
    </div>
  )
}

export default App
