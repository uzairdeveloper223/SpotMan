import React, { useState } from 'react';

export const Settings: React.FC = () => {
  const [oldPassword, setOldPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [showPassword, setShowPassword] = useState(false);

  const currentUser = localStorage.getItem('spotman_user') || 'admin';

  const handleChangePassword = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setSuccess('');

    if (newPassword !== confirmPassword) {
      setError('New passwords do not match');
      return;
    }

    if (newPassword.length < 6) {
      setError('New password must be at least 6 characters');
      return;
    }

    try {
      const token = localStorage.getItem('spotman_token');
      const res = await fetch('http://localhost:8000/api/v1/auth/change-credentials', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          old_password: oldPassword,
          new_password: newPassword
        })
      });

      if (!res.ok) {
        const data = await res.json();
        throw new Error(data.detail || 'Failed to change password');
      }

      setSuccess('Password updated successfully');
      setOldPassword('');
      setNewPassword('');
      setConfirmPassword('');
    } catch (err: any) {
      setError(err.message);
    }
  };

  return (
    <div className="p-6">
      <h1 className="text-3xl font-bold text-gray-100 mb-6">Settings</h1>

      <div className="bg-gray-800 rounded-lg border border-gray-700 shadow-sm shadow-gray-900/50 p-6">
        <div className="mb-6">
          <h2 className="text-lg font-semibold text-gray-100 mb-2">Account Information</h2>
          <div className="bg-gray-900/50 border border-gray-700 rounded p-4">
            <div className="flex flex-col gap-3">
              <div>
                <span className="text-gray-400 text-sm">Username</span>
                <p className="text-gray-200 font-mono text-lg mt-1">{currentUser}</p>
              </div>
              <div>
                <span className="text-gray-400 text-sm">Current Password</span>
                <p className="text-gray-200 font-mono text-lg mt-1">
                  {showPassword ? sessionStorage.getItem('spotman_pass') || '••••••••' : '••••••••'}
                </p>
              </div>
              <button
                onClick={() => setShowPassword(!showPassword)}
                className="text-sm text-teal-400 hover:text-teal-300 underline self-start"
              >
                {showPassword ? 'Hide password' : 'Show password'}
              </button>
            </div>
          </div>
        </div>

        <div className="border-t border-gray-700 pt-6">
          <h2 className="text-lg font-semibold text-gray-100 mb-4">Change Password</h2>

          {error && (
            <div className="bg-red-500/10 border border-red-500/50 text-red-400 p-3 rounded mb-4 text-sm">
              {error}
            </div>
          )}

          {success && (
            <div className="bg-green-500/10 border border-green-500/50 text-green-400 p-3 rounded mb-4 text-sm">
              {success}
            </div>
          )}

          <form onSubmit={handleChangePassword} className="space-y-4">
            <div>
              <label className="block text-gray-400 text-sm mb-1">Current Password</label>
              <input
                type="password"
                value={oldPassword}
                onChange={e => setOldPassword(e.target.value)}
                className="w-full bg-gray-900 border border-gray-700 rounded px-4 py-2 text-white focus:outline-none focus:border-teal-500"
                required
              />
            </div>
            <div>
              <label className="block text-gray-400 text-sm mb-1">New Password</label>
              <input
                type="password"
                value={newPassword}
                onChange={e => setNewPassword(e.target.value)}
                className="w-full bg-gray-900 border border-gray-700 rounded px-4 py-2 text-white focus:outline-none focus:border-teal-500"
                required
                minLength={6}
              />
            </div>
            <div>
              <label className="block text-gray-400 text-sm mb-1">Confirm New Password</label>
              <input
                type="password"
                value={confirmPassword}
                onChange={e => setConfirmPassword(e.target.value)}
                className="w-full bg-gray-900 border border-gray-700 rounded px-4 py-2 text-white focus:outline-none focus:border-teal-500"
                required
              />
            </div>
            <button
              type="submit"
              className="w-full bg-teal-600 hover:bg-teal-500 text-white font-bold py-2 px-4 rounded transition-colors mt-2"
            >
              Update Password
            </button>
          </form>
        </div>
      </div>
    </div>
  );
};