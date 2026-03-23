/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './src/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        // PropOS dark theme palette
        surface: {
          DEFAULT: '#0f1117',
          50: '#1a1d27',
          100: '#1e2130',
          200: '#252836',
          300: '#2d3040',
          400: '#363a4a',
        },
        accent: {
          DEFAULT: '#6366f1',  // Indigo
          light: '#818cf8',
          dark: '#4f46e5',
          glow: 'rgba(99, 102, 241, 0.15)',
        },
        success: {
          DEFAULT: '#22c55e',
          light: '#4ade80',
          glow: 'rgba(34, 197, 94, 0.15)',
        },
        danger: {
          DEFAULT: '#ef4444',
          light: '#f87171',
          glow: 'rgba(239, 68, 68, 0.15)',
        },
        warning: {
          DEFAULT: '#f59e0b',
          light: '#fbbf24',
          glow: 'rgba(245, 158, 11, 0.15)',
        },
        muted: '#9ca3af',
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        mono: ['JetBrains Mono', 'monospace'],
      },
      boxShadow: {
        glass: '0 8px 32px rgba(0, 0, 0, 0.3)',
        glow: '0 0 20px rgba(99, 102, 241, 0.2)',
        'glow-success': '0 0 20px rgba(34, 197, 94, 0.2)',
        'glow-danger': '0 0 20px rgba(239, 68, 68, 0.2)',
      },
      backdropBlur: {
        glass: '16px',
      },
      animation: {
        'pulse-slow': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'glow-pulse': 'glow-pulse 2s ease-in-out infinite alternate',
      },
      keyframes: {
        'glow-pulse': {
          '0%': { boxShadow: '0 0 5px rgba(99, 102, 241, 0.2)' },
          '100%': { boxShadow: '0 0 20px rgba(99, 102, 241, 0.4)' },
        },
      },
    },
  },
  plugins: [],
};
