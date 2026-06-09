import React from 'react';
import { Outlet, Link } from 'react-router-dom';
import { LivePulse } from '../components/atoms/LivePulse';

export default function PublicLayout() {
  return (
    <div className="min-h-screen flex flex-col bg-bg-primary text-text-primary">
      <header className="bg-bg-card border-b border-border py-4 px-6 flex justify-between items-center shadow-sm">
        <div className="flex flex-col md:flex-row md:items-center gap-1 md:gap-4">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-md bg-accent-red flex items-center justify-center text-white font-bold font-mono">
              RG
            </div>
            <span className="font-bold text-lg tracking-tight">ReliefGrid</span>
          </div>
          <span className="text-sm text-text-muted hidden md:inline-block border-l border-border pl-4">
            Emergency Response Platform
          </span>
        </div>
        <nav className="flex gap-4 sm:gap-6 items-center">
          <div className="hidden sm:block">
            <LivePulse />
          </div>
          <Link to="/login" className="px-4 py-2 bg-transparent text-text-primary border border-border rounded font-medium hover:bg-bg-secondary transition-colors text-sm">
            Login &rarr;
          </Link>

        </nav>
      </header>
      
      <main className="flex-grow">
        <Outlet />
      </main>
      
      <footer className="border-t border-border py-6 text-center text-text-muted text-sm bg-bg-card">
        &copy; {new Date().getFullYear()} ReliefGrid Coordination Platform. Official use only.
      </footer>
    </div>
  );
}
