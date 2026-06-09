import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { usePageTitle } from '../hooks/usePageTitle';

export default function AdminLogin() {
  const [role, setRole] = useState('admin'); // 'admin' | 'volunteer'
  usePageTitle(role === 'admin' ? 'Admin Login' : 'Volunteer Login');
  const [pin, setPin] = useState('');
  const [volunteerName, setVolunteerName] = useState('');
  const [error, setError] = useState('');
  const [shake, setShake] = useState(false);
  const navigate = useNavigate();

  const handleSubmit = (e) => {
    e.preventDefault();
    if (role === 'admin') {
      if (pin === '123456') {
        localStorage.setItem('aria_pin', 'aria2026');
        localStorage.setItem('user_role', 'admin');
        localStorage.setItem('relief_auth', 'true');
        navigate('/admin/dashboard');
      } else {
        setError('Invalid Admin PIN');
        setPin('');
        setShake(true);
        setTimeout(() => setShake(false), 500);
      }
    } else {
      if (!volunteerName.trim()) {
        setError('Please enter your name');
        setShake(true);
        setTimeout(() => setShake(false), 500);
        return;
      }
      if (pin === '654321') {
        localStorage.setItem('aria_pin', 'volunteer2026');
        localStorage.setItem('user_role', 'volunteer');
        localStorage.setItem('relief_auth', 'true');
        localStorage.setItem('volunteer_name', volunteerName);
        localStorage.setItem('volunteer_email', `${volunteerName.toLowerCase().replace(/\s+/g, '')}@reliefgrid.org`);
        localStorage.setItem('volunteer_phone', '9876543210');
        navigate('/volunteer/dashboard');
      } else {
        setError('Invalid Volunteer PIN');
        setPin('');
        setShake(true);
        setTimeout(() => setShake(false), 500);
      }
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-[#1A1714] text-white">
      <motion.div 
        animate={shake ? { x: [-10, 10, -10, 10, 0] } : {}}
        transition={{ duration: 0.4 }}
        className="w-full max-w-md p-8 bg-[#211E1A] border border-gray-800 rounded-lg shadow-2xl"
      >
        <div className="flex flex-col items-center mb-6 text-center">
          <div className="flex items-center gap-2 mb-3">
            <div className="w-10 h-10 rounded-md bg-accent-red flex items-center justify-center text-white font-bold font-mono text-xl shadow-lg">
              RG
            </div>
            <span className="font-bold text-2xl tracking-tight text-white">ReliefGrid</span>
          </div>
          <p className="text-sm text-gray-400 font-mono tracking-widest uppercase">Operations Console</p>
        </div>

        {/* Role Switcher */}
        <div className="flex bg-[#1A1714] rounded-lg p-1 mb-6 border border-gray-800">
          <button
            type="button"
            onClick={() => { setRole('admin'); setError(''); setPin(''); }}
            className={`flex-1 py-2 text-xs font-bold uppercase tracking-wider rounded transition-all duration-150 ${
              role === 'admin' ? 'bg-accent-blue text-white shadow-md' : 'text-gray-500 hover:text-gray-300'
            }`}
          >
            Admin
          </button>
          <button
            type="button"
            onClick={() => { setRole('volunteer'); setError(''); setPin(''); }}
            className={`flex-1 py-2 text-xs font-bold uppercase tracking-wider rounded transition-all duration-150 ${
              role === 'volunteer' ? 'bg-accent-blue text-white shadow-md' : 'text-gray-500 hover:text-gray-300'
            }`}
          >
            Volunteer
          </button>
        </div>

        <form onSubmit={handleSubmit} className="space-y-5">
          {role === 'volunteer' && (
            <div>
              <label htmlFor="volunteerName" className="block text-xs font-bold text-gray-500 uppercase tracking-wider mb-2">
                Full Name
              </label>
              <input
                id="volunteerName"
                type="text"
                value={volunteerName}
                onChange={(e) => {
                  setVolunteerName(e.target.value);
                  if (error) setError('');
                }}
                className="w-full px-4 py-3 bg-[#1A1714] border border-gray-800 rounded-lg text-white text-base focus:outline-none focus:border-accent-blue transition-colors"
                placeholder="Enter your name"
                required
                autoFocus
              />
            </div>
          )}

          <div>
            <label htmlFor="pin" className="block text-xs font-bold text-gray-500 uppercase tracking-wider mb-2 text-center">
              {role === 'admin' ? 'Enter Admin PIN' : 'Enter Volunteer PIN'}
            </label>
            <input
              id="pin"
              type="password"
              value={pin}
              onChange={(e) => {
                setPin(e.target.value);
                if (error) setError('');
              }}
              className={`w-full px-4 py-3 bg-[#1A1714] border-2 rounded-lg text-center text-white font-mono text-xl tracking-[0.3em] focus:outline-none transition-colors ${
                error ? 'border-accent-red focus:border-accent-red' : 'border-gray-800 focus:border-accent-blue'
              }`}
              placeholder="••••••"
              autoFocus={role === 'admin'}
            />
            {error && <p className="text-accent-red text-sm mt-2 font-mono text-center font-bold">{error}</p>}
          </div>

          <button
            type="submit"
            className="w-full py-4 bg-accent-blue text-white font-bold text-lg rounded-lg hover:bg-blue-600 transition-colors shadow-lg shadow-accent-blue/20"
          >
            Authenticate
          </button>
        </form>
        
        <div className="mt-8 pt-6 border-t border-gray-800 text-center">
          <p className="text-xs text-gray-500 font-mono">
            {role === 'admin' ? 'Authorized personnel only. All actions are logged.' : 'Register/Log in to view assignments.'}
          </p>
          <a href="/" className="inline-block mt-4 text-sm text-gray-400 hover:text-white transition-colors">
            &larr; Return to Public Portal
          </a>
        </div>
      </motion.div>
    </div>
  );
}

