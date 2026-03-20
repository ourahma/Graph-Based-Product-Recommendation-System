'use client';

import React from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import {
  BarChart3,
  Sparkles,
  Users,
  TrendingUp,
  Settings,
  Home,
  Network,
  Package,
} from 'lucide-react';

interface LayoutProps {
  children: React.ReactNode;
}

const Layout: React.FC<LayoutProps> = ({ children }) => {
  const pathname = usePathname();

  const isActive = (path: string) => pathname === path;

  const navItems = [
    { label: 'Dashboard', href: '/', icon: Home },
    { label: 'Recommendations', href: '/recommendations', icon: Sparkles },
    { label: 'Customers', href: '/customers', icon: Users },
    { label: 'Products', href: '/products', icon: Package },
    { label: 'Analytics', href: '/analytics', icon: BarChart3 },
    { label: 'Graph Network', href: '/graph', icon: Network },
    { label: 'Admin', href: '/admin', icon: Settings },
  ];

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900">
      {/* Sidebar Navigation */}
      <nav className="fixed left-0 top-0 h-screen w-64 glass-dark border-r border-slate-700 p-6 backdrop-blur-xl">
        <Link href="/" className="mb-12 flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-gradient-to-br from-primary-500 to-accent-500">
            <Network className="text-white" size={24} />
          </div>
          <span className="gradient-text text-xl font-bold">RecSys</span>
        </Link>

        <div className="space-y-2">
          {navItems.map((item) => {
            const Icon = item.icon;
            const active = isActive(item.href);

            return (
              <Link
                key={item.href}
                href={item.href}
                className={`flex items-center gap-3 rounded-lg px-4 py-3 transition-all duration-200 ${
                  active
                    ? 'bg-gradient-to-r from-primary-500 to-accent-500 text-white shadow-lg shadow-primary-500/50'
                    : 'text-slate-300 hover:bg-white/10 hover:text-white'
                }`}
              >
                <Icon size={20} />
                <span className="font-medium">{item.label}</span>
              </Link>
            );
          })}
        </div>
      </nav>

      {/* Main Content */}
      <main className="ml-64 min-h-screen p-8">
        {/* Top Bar */}
        <div className="mb-8 flex items-center justify-between rounded-2xl glass bg-white/5 px-8 py-4 backdrop-blur-xl">
          <h1 className="text-2xl font-bold">
            <span className="gradient-text">Recommendation Engine</span>
          </h1>
          <div className="flex items-center gap-4">
            <div className="flex items-center gap-2 rounded-lg bg-white/10 px-4 py-2">
              <div className="h-3 w-3 rounded-full bg-green-400 animate-pulse"></div>
              <span className="text-sm text-slate-300">System Active</span>
            </div>
          </div>
        </div>

        {/* Content */}
        <div className="animate-fade-in">{children}</div>
      </main>
    </div>
  );
};

export default Layout;
