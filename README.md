# PaperTrade — Local Paper Trading Dashboard

A paper trading terminal with a 2×2 TradingView-style chart grid, positions panel, and API for ClawBot integration.

---

## Quick Start

```bash
cd paper-trading
chmod +x start.sh
./start.sh
```

Then open **http://localhost:5000** in your browser.

---

## API Reference

### Open a Trade (ClawBot uses this)
```
POST /api/create
Content-Type: application/json

{
  "symbol": "LINK/USDT",
  "direction": "LONG",
  "entry_low": 8.494,
  "entry_high": 8.757,
  "take_profits": [8.800, 9.061, 9.323, 9.584, 9.845],
  "stop_loss": 8.14401
}
```

### Get All Trades (paginated)
```
GET /api/trades?page=1&per_page=4
```

### Update Trade Status
```
PATCH /api/trades/<id>
{ "status": "success" | "failed" | "open" | "partial", "pnl": 0.15 }
```

### Delete a Trade
```
DELETE /api/trades/<id>
```

### Stats
```
GET /api/stats
```

---

## ClawBot Setup

1. Copy `CLAWBOT_PROMPT.md` contents into your ClawBot system prompt
2. Make sure the API server is running at `http://localhost:5000`
3. Send your trading signal to ClawBot — it will parse and POST it automatically

---

## Features

- ✅ 2×2 chart grid per page, multi-page navigation
- ✅ Charts draw entry zone, TP levels, and SL as horizontal lines
- ✅ Positions panel on the right with P&L, status badges
- ✅ Mark trades as Win / Loss / Delete
- ✅ SQLite persistence
- ✅ REST API for ClawBot integration
- ✅ Auto-refresh every 30 seconds

---

## File Structure

```
paper-trading/
├── app.py              # Flask backend + SQLite
├── requirements.txt    
├── start.sh            # Run this to start
├── trades.db           # Auto-created SQLite database
├── frontend/
│   └── index.html      # Full dashboard UI
└── CLAWBOT_PROMPT.md   # Give this to your ClawBot
```
