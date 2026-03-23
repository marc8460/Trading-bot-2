# PropOS — Multi-Account Prop Trading Operating System

A production-oriented, MT5-first forex prop trading platform supporting multiple prop firm accounts with intelligent trade routing, compliance enforcement, and real-time monitoring.

## Features

- **Strategy Engine** — Swappable strategies for EURUSD, XAUUSD, GBPUSD
- **Multi-Account Execution** — One signal → many accounts with per-account sizing
- **Prop Firm Compliance** — E8, FTMO, FundedNext, The5ers rule profiles
- **Risk Management** — Per-trade, per-account, and cross-account risk control
- **Real-Time Dashboard** — Dark-mode Next.js dashboard with live data
- **Telegram Alerts** — Trade notifications, warnings, kill switch
- **VPS-Ready** — Docker deployment for 24/7 operation

## Quick Start

### Backend
```bash
# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # or .venv\Scripts\activate on Windows

# Install dependencies
pip install -e ".[dev]"

# Copy and configure environment
cp .env.example .env
# Edit .env with your MT5 credentials and Telegram token

# Run
python -m backend.main
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```

### Docker
```bash
docker-compose up -d
```

## Architecture

```
Market Data → Strategy → Filters → Risk → Compliance → Router → Execution → Monitoring → Telegram
```

See `docs/` for full architecture documentation.

## Configuration

- `.env` — Secrets (MT5 passwords, API keys)
- `config/settings.yaml` — Global system settings
- `config/accounts.yaml` — MT5 account definitions
- `config/firms/*.yaml` — Prop firm compliance profiles

## License

Proprietary — All rights reserved.
