import os
import json
from datetime import datetime
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__, static_folder='frontend')
CORS(app)

# Supabase Config
SUPABASE_URL = os.environ.get("NEXT_PUBLIC_SUPABASE_URL") or os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("NEXT_PUBLIC_SUPABASE_KEY") or os.environ.get("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    print("⚠️ SUPABASE_URL or SUPABASE_KEY not set. Local logic might fail.")
    supabase = None
else:
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def format_trade(t):
    # Supabase returns numeric as float/decimal, timestamps as strings
    return t

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

    trade_data = {
        "symbol": data['symbol'].upper(),
        "direction": data['direction'].upper(),
        "entry_low": float(data['entry_low']),
        "entry_high": float(data['entry_high']),
        "take_profits": data['take_profits'], # Supabase handles JSONB
        "stop_loss": float(data['stop_loss']),
        "status": "open"
    }

    try:
        response = supabase.table("trades").insert(trade_data).execute()
        return jsonify({'success': True, 'trade': response.data[0]}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/trades', methods=['GET'])
def get_trades():
    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 4))
    status = request.args.get('status')

    try:
        query = supabase.table("trades").select("*", count="exact").order("created_at", desc=True)
        if status:
            query = query.eq("status", status)
        
        # Pagination
        start = (page - 1) * per_page
        end = start + per_page - 1
        response = query.range(start, end).execute()
        
        total = response.count
        return jsonify({
            'trades': response.data,
            'total': total,
            'page': page,
            'per_page': per_page,
            'total_pages': max(1, (total + per_page - 1) // per_page)
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/trades/<int:trade_id>', methods=['PATCH'])
def update_trade(trade_id):
    data = request.get_json()
    allowed = ['status', 'pnl', 'notes']
    update_data = {}
    for field in allowed:
        if field in data:
            update_data[field] = data[field]
    
    if 'status' in data and data['status'] in ['success', 'failed']:
        update_data['closed_at'] = datetime.utcnow().isoformat()

    try:
        response = supabase.table("trades").update(update_data).eq("id", trade_id).execute()
        return jsonify({'success': True, 'trade': response.data[0]})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/trades/<int:trade_id>', methods=['DELETE'])
def delete_trade(trade_id):
    try:
        supabase.table("trades").delete().eq("id", trade_id).execute()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/stats', methods=['GET'])
def get_stats():
    try:
        response = supabase.table("trades").select("status", "pnl").execute()
        rows = response.data
        total = len(rows)
        wins = sum(1 for r in rows if r['status'] == 'success')
        losses = sum(1 for r in rows if r['status'] == 'failed')
        total_pnl = sum(r.get('pnl', 0) or 0 for r in rows)
        return jsonify({'total': total, 'wins': wins, 'losses': losses, 'total_pnl': round(total_pnl, 4)})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5001)
