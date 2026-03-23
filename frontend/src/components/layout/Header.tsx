'use client';

export function Header() {
  return (
    <header className="h-14 border-b border-surface-300/30 bg-surface-50/80 backdrop-blur-xl flex items-center justify-between px-6">
      {/* Left: Page context */}
      <div className="flex items-center gap-4">
        <h2 className="text-sm font-semibold text-gray-200">Dashboard</h2>
        <span className="text-xs text-muted">Real-time trading overview</span>
      </div>

      {/* Right: Status indicators */}
      <div className="flex items-center gap-6">
        {/* Connection status */}
        <div className="flex items-center gap-2 text-xs">
          <div className="status-dot status-dot-active" />
          <span className="text-muted">MT5 Connected</span>
        </div>

        {/* Time */}
        <div className="text-xs font-mono text-muted">
          {new Date().toLocaleTimeString('en-US', { hour12: false })}
        </div>

        {/* Alert badge */}
        <div className="relative">
          <span className="text-muted text-sm cursor-pointer hover:text-white transition-colors">🔔</span>
          <div className="absolute -top-1 -right-1 w-3 h-3 bg-danger rounded-full text-[8px] text-white flex items-center justify-center">
            2
          </div>
        </div>
      </div>
    </header>
  );
}
