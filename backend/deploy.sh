#!/bin/bash

echo "Pulling latest code..."
git pull origin main

echo "Installing dependencies..."
pip install -r requirements.txt

echo "Restarting backend..."
pkill -f uvicorn
nohup python3.11 -m uvicorn app.main:app --host 0.0.0.0 --port 8000 > app.log 2>&1 &

echo "Deployment complete"
