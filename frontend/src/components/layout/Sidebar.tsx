'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';

const navItems = [
  { href: '/', label: 'Dashboard', icon: '◆' },
  { href: '/accounts', label: 'Accounts', icon: '◎' },
  { href: '/trades', label: 'Trades', icon: '⇄' },
  { href: '/compliance', label: 'Compliance', icon: '◈' },
  { href: '/settings', label: 'Settings', icon: '⚙' },
];

export function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="w-64 h-screen bg-surface-50 border-r border-surface-300/50 flex flex-col">
      {/* Logo */}
      <div className="p-6 border-b border-surface-300/30">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-lg bg-gradient-to-br from-accent to-accent-light flex items-center justify-center shadow-glow">
            <span className="text-white font-bold text-sm">P</span>
          </div>
          <div>
            <h1 className="text-lg font-bold text-gradient">PropOS</h1>
            <p className="text-[10px] text-muted tracking-widest uppercase">Trading System</p>
          </div>
        </div>
      </div>

      {/* Navigation */}
      <nav className="flex-1 p-4 space-y-1">
        {navItems.map((item) => (
          <Link
            key={item.href}
            href={item.href}
            className={`nav-link ${pathname === item.href ? 'nav-link-active' : ''}`}
          >
            <span className="text-base w-5 text-center">{item.icon}</span>
            <span>{item.label}</span>
          </Link>
        ))}
      </nav>

      {/* Footer */}
      <div className="p-4 border-t border-surface-300/30">
        <div className="flex items-center gap-2 text-xs text-muted">
          <div className="status-dot status-dot-active" />
          <span>System Online</span>
        </div>
        <p className="text-[10px] text-surface-400 mt-1">v1.0.0</p>
      </div>
    </aside>
  );
}
