# Personal Real-Time Risk Monitor (No Auto-Trading)

This project is a monitoring-only dashboard for Solana token risk and signal tracking, with a separate Polymarket signal stream. It does **not** execute trades.

## What You Get
- Real-time polling loop for potential Solana coins.
- Risk scoring model (rug-risk style checks).
- Scenario-based potential gain/downside estimate (not a guarantee).
- Unified dashboard feed (Solana + Polymarket signals).
- SSE live event stream for low-latency UI updates.

## Reliability Design
- Provider adapters are isolated (`app/adapters`), so one failing data source does not crash the monitor.
- Safe JSON fetch wrappers degrade gracefully to empty data.
- In-memory rolling event buffer prevents unbounded memory growth.
- Start/stop controls let you recover quickly when a provider is unstable.
- Fallback sample data keeps local development usable without API keys.

## Architecture
- `app/adapters/solana_adapter.py`: Solana candidate discovery + signal collection.
- `app/adapters/polymarket_adapter.py`: separate Polymarket signal pipeline.
- `app/services/scoring.py`: deterministic risk score and reasons.
- `app/services/estimator.py`: potential upside/downside and EV model.
- `app/services/monitor.py`: polling loop, state, event stream data.
- `app/api/routes.py`: REST + SSE endpoints.
- `web/`: lightweight live dashboard.

## Setup
1. `python -m venv .venv`
2. `.\.venv\Scripts\Activate.ps1`
3. `python -m pip install -r requirements.txt`
4. Copy `.env.example` to `.env` and set optional API keys.
5. `uvicorn app.main:app --reload`
6. Open `http://127.0.0.1:8000`

## API Endpoints
- `POST /api/monitor/start`
- `POST /api/monitor/stop`
- `GET /api/monitor/state`
- `GET /api/risk/top`
- `GET /api/gain/top`
- `GET /api/signals/unified`
- `GET /api/stream` (SSE)

## Important Notes
- Output is a decision-support signal, not financial advice.
- EV model is scenario-based and may diverge from live market behavior.
- No method can guarantee safety from rug pulls.
