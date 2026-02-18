from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import sqlite3
import json
import os
from datetime import datetime

# Use /tmp for SQLite on Vercel as it's the only writable directory
IS_VERCEL = "VERCEL" in os.environ
DB_PATH = '/tmp/trades.db' if IS_VERCEL else 'trades.db'

app = Flask(__name__, static_folder='frontend')

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with get_db() as conn:
        conn.execute('''
            CREATE TABLE IF NOT EXISTS trades (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT NOT NULL,
                direction TEXT NOT NULL,
                entry_low REAL NOT NULL,
                entry_high REAL NOT NULL,
                take_profits TEXT NOT NULL,
                stop_loss REAL NOT NULL,
                status TEXT DEFAULT 'open',
                created_at TEXT NOT NULL,
                closed_at TEXT,
                pnl REAL DEFAULT 0,
                notes TEXT
            )
        ''')
        conn.commit()

def row_to_dict(row):
    d = dict(row)
    d['take_profits'] = json.loads(d['take_profits'])
    return d

@app.before_request
def ensure_db_initialized():
    init_db()

@app.route('/')
def index():
    return send_from_directory('frontend', 'index.html')

@app.route('/api/create', methods=['POST'])
def create_trade():
    data = request.get_json()
    required = ['symbol', 'direction', 'entry_low', 'entry_high', 'take_profits', 'stop_loss']
    for field in required:
        if field not in data:
            return jsonify({'error': f'Missing field: {field}'}), 400

    direction = data['direction'].upper()
    if direction not in ['LONG', 'SHORT']:
        return jsonify({'error': 'direction must be LONG or SHORT'}), 400

    with get_db() as conn:
        cur = conn.execute('''
            INSERT INTO trades (symbol, direction, entry_low, entry_high, take_profits, stop_loss, status, created_at)
            VALUES (?, ?, ?, ?, ?, ?, 'open', ?)
        ''', (
            data['symbol'].upper(),
            direction,
            float(data['entry_low']),
            float(data['entry_high']),
            json.dumps([float(tp) for tp in data['take_profits']]),
            float(data['stop_loss']),
            datetime.utcnow().isoformat()
        ))
        trade_id = cur.lastrowid
        conn.commit()

    trade = row_to_dict(conn.execute('SELECT * FROM trades WHERE id = ?', (trade_id,)).fetchone())
    return jsonify({'success': True, 'trade': trade}), 201

@app.route('/api/trades', methods=['GET'])
def get_trades():
    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 4))
    status = request.args.get('status')

    with get_db() as conn:
        query = 'SELECT * FROM trades'
        params = []
        if status:
            query += ' WHERE status = ?'
            params.append(status)
        query += ' ORDER BY created_at DESC'

        all_trades = [row_to_dict(r) for r in conn.execute(query, params).fetchall()]
        total = len(all_trades)
        start = (page - 1) * per_page
        trades = all_trades[start:start + per_page]

    return jsonify({
        'trades': trades,
        'total': total,
        'page': page,
        'per_page': per_page,
        'total_pages': max(1, (total + per_page - 1) // per_page)
    })

@app.route('/api/trades/<int:trade_id>', methods=['GET'])
def get_trade(trade_id):
    with get_db() as conn:
        row = conn.execute('SELECT * FROM trades WHERE id = ?', (trade_id,)).fetchone()
        if not row:
            return jsonify({'error': 'Trade not found'}), 404
        return jsonify(row_to_dict(row))

@app.route('/api/trades/<int:trade_id>', methods=['PATCH'])
def update_trade(trade_id):
    data = request.get_json()
    with get_db() as conn:
        row = conn.execute('SELECT * FROM trades WHERE id = ?', (trade_id,)).fetchone()
        if not row:
            return jsonify({'error': 'Trade not found'}), 404

        updates = []
        params = []
        allowed = ['status', 'pnl', 'notes', 'closed_at']
        for field in allowed:
            if field in data:
                updates.append(f'{field} = ?')
                params.append(data[field])

        if 'status' in data and data['status'] in ['success', 'failed']:
            updates.append('closed_at = ?')
            params.append(datetime.utcnow().isoformat())

        if updates:
            params.append(trade_id)
            conn.execute(f'UPDATE trades SET {", ".join(updates)} WHERE id = ?', params)
            conn.commit()

        trade = row_to_dict(conn.execute('SELECT * FROM trades WHERE id = ?', (trade_id,)).fetchone())
        return jsonify({'success': True, 'trade': trade})

@app.route('/api/trades/<int:trade_id>', methods=['DELETE'])
def delete_trade(trade_id):
    with get_db() as conn:
        conn.execute('DELETE FROM trades WHERE id = ?', (trade_id,))
        conn.commit()
    return jsonify({'success': True})

@app.route('/api/stats', methods=['GET'])
def get_stats():
    with get_db() as conn:
        rows = conn.execute('SELECT status, pnl FROM trades').fetchall()
        total = len(rows)
        wins = sum(1 for r in rows if r['status'] == 'success')
        losses = sum(1 for r in rows if r['status'] == 'failed')
        total_pnl = sum(r['pnl'] or 0 for r in rows)
    return jsonify({'total': total, 'wins': wins, 'losses': losses, 'total_pnl': round(total_pnl, 4)})

if __name__ == '__main__':
    init_db()
    app.run(debug=True, port=5001)
