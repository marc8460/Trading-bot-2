'use client';

import { useState } from 'react';

export function ControlPanel() {
  const [isRunning, setIsRunning] = useState(true);
  const [riskLevel, setRiskLevel] = useState(60);

  return (
    <div className="glass-card p-5 space-y-4">
      <h3 className="text-sm font-medium text-muted">Controls</h3>

      {/* Start/Stop */}
      <div className="flex gap-2">
        <button
          onClick={() => setIsRunning(true)}
          className={`flex-1 py-2 rounded-lg text-sm font-medium transition-all duration-200
            ${isRunning
              ? 'bg-success/20 text-success border border-success/30'
              : 'btn-outline'
            }`}
        >
          Start
        </button>
        <button
          onClick={() => setIsRunning(false)}
          className={`flex-1 py-2 rounded-lg text-sm font-medium transition-all duration-200
            ${!isRunning
              ? 'bg-danger/20 text-danger border border-danger/30'
              : 'btn-outline'
            }`}
        >
          Stop
        </button>
      </div>

      {/* Kill Switch */}
      <button className="w-full btn-danger flex items-center justify-center gap-2 py-3">
        <span>☠</span>
        <span>Kill Switch</span>
      </button>

      {/* Risk Slider */}
      <div className="space-y-2">
        <div className="flex justify-between text-xs">
          <span className="text-muted">Risk Level</span>
          <span className="font-mono text-gray-200">{riskLevel}%</span>
        </div>
        <input
          type="range"
          min="0"
          max="100"
          value={riskLevel}
          onChange={(e) => setRiskLevel(Number(e.target.value))}
          className="w-full h-2 bg-surface-300 rounded-full appearance-none cursor-pointer
            [&::-webkit-slider-thumb]:appearance-none
            [&::-webkit-slider-thumb]:w-4 [&::-webkit-slider-thumb]:h-4
            [&::-webkit-slider-thumb]:rounded-full [&::-webkit-slider-thumb]:bg-accent
            [&::-webkit-slider-thumb]:shadow-glow [&::-webkit-slider-thumb]:cursor-pointer"
        />
        <div className="flex justify-between text-[10px] text-surface-400">
          <span>Conservative</span>
          <span>Aggressive</span>
        </div>
      </div>
    </div>
  );
}
