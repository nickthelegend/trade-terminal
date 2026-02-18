#!/bin/bash
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  PAPERTRADE — Local Server"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Install deps if needed
pip install flask flask-cors --break-system-packages -q

echo "► Starting server on http://localhost:5000"
echo "► Dashboard: http://localhost:5000"
echo "► API:       http://localhost:5000/api"
echo ""
echo "ClawBot endpoint: POST http://localhost:5000/api/create"
echo ""

python app.py
