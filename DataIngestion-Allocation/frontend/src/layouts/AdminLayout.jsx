import React, { useEffect, useState } from 'react';
import { Outlet, NavLink, useNavigate } from 'react-router-dom';
import { Menu, X, LayoutDashboard, History } from 'lucide-react';
import { SystemStatusPanel } from '../components';
import { api } from '../services/api';

export default function AdminLayout() {
  const navigate = useNavigate();
  const [stats, setStats] = useState({ pending: 0, open: 0 });
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);

  useEffect(() => {
    const fetchStats = async () => {
      const [pendingRes, publicRes] = await Promise.all([
        api.getPendingApprovalCards(),
        api.getPublicNeedCards()
      ]);
      setStats({
        pending: pendingRes.data?.length || 0,
        open: publicRes.data?.length || 0
      });
    };
    fetchStats();
    
    const interval = setInterval(fetchStats, 10000);
    return () => clearInterval(interval);
  }, []);

  const handleLogout = () => {
    localStorage.removeItem('aria_pin');
    localStorage.removeItem('relief_auth');
    navigate('/admin/login');
  };

  const navLinks = [
    { to: '/admin', label: 'Dashboard', icon: LayoutDashboard, end: true },
    { to: '/admin/audit-log', label: 'Audit Log', icon: History },
  ];

  return (
    <div className="min-h-screen flex bg-bg-secondary text-text-primary">
      {/* Mobile Menu Overlay */}
      {isMobileMenuOpen && (
        <div 
          className="fixed inset-0 bg-black/50 z-40 md:hidden"
          onClick={() => setIsMobileMenuOpen(false)}
        />
      )}

      {/* Sidebar */}
      <aside className={`
        fixed inset-y-0 left-0 z-50 flex flex-col flex-shrink-0 bg-sidebar-bg text-sidebar-text transition-all duration-300 ease-in-out
        w-[240px] transform ${isMobileMenuOpen ? 'translate-x-0' : '-translate-x-full'}
        md:relative md:translate-x-0 md:w-[60px] lg:w-[240px] overflow-hidden
      `}>
        {/* ReliefGrid Logo Area */}
        <div className="h-14 md:h-16 flex items-center p-4 border-b border-gray-800">
          <div className="flex items-center gap-3 w-full">
            <div className="w-8 h-8 flex-shrink-0 bg-accent-blue rounded flex items-center justify-center font-mono font-bold text-white shadow-sm">
              RG
            </div>
            <div className="md:hidden lg:block whitespace-nowrap overflow-hidden">
              <h1 className="font-bold tracking-wider text-white leading-tight">RELIEFGRID</h1>
              <p className="text-[10px] text-gray-400 font-mono uppercase tracking-widest mt-0.5">Admin Console</p>
            </div>
          </div>
          <button 
            className="md:hidden text-gray-400 hover:text-white"
            onClick={() => setIsMobileMenuOpen(false)}
          >
            <X size={20} />
          </button>
        </div>

        {/* Nav Links */}
        <nav className="flex-grow py-4 px-2 flex flex-col gap-2">
          {navLinks.map((link) => (
            <NavLink 
              key={link.to}
              to={link.to} 
              end={link.end}
              onClick={() => setIsMobileMenuOpen(false)}
              className={({ isActive }) => 
                `flex items-center gap-3 px-3 py-2.5 rounded-md transition-colors text-sm font-medium whitespace-nowrap
                ${isActive ? 'bg-gray-800 text-white' : 'text-gray-400 hover:bg-gray-800/50 hover:text-gray-200'}`
              }
            >
              <link.icon size={18} className="flex-shrink-0" />
              <span className="md:hidden lg:inline">{link.label}</span>
            </NavLink>
          ))}
        </nav>

        {/* System Status Widget (Hidden on tablet icon-only view) */}
        <div className="p-4 border-t border-gray-800 md:hidden lg:block">
          <h3 className="text-xs font-bold text-gray-500 uppercase tracking-wider mb-3">System Status</h3>
          <SystemStatusPanel 
            pendingCount={stats.pending} 
            openNeedsCount={stats.open} 
          />
        </div>
      </aside>

      {/* Main Content Area */}
      <main className="flex-grow flex flex-col h-screen overflow-hidden min-w-0">
        {/* Admin Topbar */}
        <header className="h-14 bg-bg-card border-b border-border flex items-center justify-between px-4 sm:px-6 shrink-0 shadow-sm relative z-30">
          <div className="flex items-center gap-3">
            <button 
              className="md:hidden text-text-secondary hover:text-text-primary mr-1"
              onClick={() => setIsMobileMenuOpen(true)}
            >
              <Menu size={20} />
            </button>
            <span className="text-sm font-bold text-text-primary tracking-tight hidden sm:inline">ReliefGrid Operations Console</span>
            <span className="text-sm font-bold text-text-primary tracking-tight sm:hidden">ReliefGrid Admin</span>
            <span className="px-2 py-0.5 bg-accent-red/10 text-accent-red rounded text-[10px] font-bold uppercase tracking-wider font-mono hidden sm:inline">Live Env</span>
          </div>
          
          <div className="flex items-center gap-4 sm:gap-6">
            <div className="text-sm hidden sm:block">
              <span className="text-text-muted mr-2">Admin:</span>
              <span className="font-bold font-mono text-text-primary">System Auth</span>
            </div>
            <button 
              onClick={handleLogout}
              className="text-sm text-accent-red font-bold hover:text-red-800 transition-colors"
            >
              Log Out
            </button>
          </div>
        </header>
        
        {/* Scrollable content */}
        <div className="flex-grow overflow-auto p-4 sm:p-6 lg:p-8 relative">
          <div className="max-w-[1400px] mx-auto">
            <Outlet />
          </div>
        </div>
      </main>
    </div>
  );
}
