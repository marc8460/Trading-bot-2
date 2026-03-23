interface SystemHealthProps {
  status: 'running' | 'stopped' | 'error' | 'kill_switch';
  uptime: string;
}

export function SystemHealth({ status, uptime }: SystemHealthProps) {
  const statusConfig: Record<string, { label: string; dot: string; bg: string }> = {
    running: { label: 'Online', dot: 'status-dot-active', bg: 'bg-success/5 border-success/20' },
    stopped: { label: 'Stopped', dot: 'status-dot-inactive', bg: 'bg-danger/5 border-danger/20' },
    error: { label: 'Error', dot: 'status-dot-inactive', bg: 'bg-danger/5 border-danger/20' },
    kill_switch: { label: 'KILL SWITCH', dot: 'status-dot-inactive', bg: 'bg-danger/10 border-danger/30' },
  };

  const config = statusConfig[status] || statusConfig.stopped;

  return (
    <div className={`metric-card border ${config.bg}`}>
      <span className="metric-label">System Status</span>
      <div className="flex items-center gap-2">
        <div className={`status-dot ${config.dot}`} />
        <span className="text-lg font-bold text-gray-100">{config.label}</span>
      </div>
      <span className="text-xs text-muted font-mono">Uptime: {uptime}</span>
    </div>
  );
}
