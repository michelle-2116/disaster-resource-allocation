import React from 'react';
import { Link } from 'react-router-dom';
import { usePageTitle } from '../hooks/usePageTitle';

export default function NotFound() {
  usePageTitle('Page Not Found');
  return (
    <div className="min-h-screen flex flex-col items-center justify-center bg-bg-primary text-text-primary px-6">
      <div className="text-center">
        <h1 className="text-6xl font-mono font-bold text-accent-red mb-4">404</h1>
        <h2 className="text-2xl font-bold tracking-tight mb-6">Page Not Found</h2>
        <p className="text-text-secondary mb-8">The requested page does not exist or has been moved.</p>
        <Link 
          to="/"
          className="px-6 py-3 bg-text-primary text-white font-bold rounded shadow-sm hover:bg-gray-800 transition-colors"
        >
          Back to Dashboard
        </Link>
      </div>
    </div>
  );
}
