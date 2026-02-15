#!/usr/bin/env bash
cd "$(dirname "$0")"
./venv/bin/python app.py & PID=$!
sleep 2
xdg-open http://127.0.0.1:5000
echo ""
echo "Server running at http://127.0.0.1:5000 — Press Enter to stop."
read
kill $PID 2>/dev/null
