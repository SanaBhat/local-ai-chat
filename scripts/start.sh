#!/bin/bash

# LocalAI Chat Startup Script

set -e

echo "🚀 Starting LocalAI Chat..."

# Activate virtual environment
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Check if models directory exists
if [ ! -d "models" ]; then
    echo "📁 Creating models directory..."
    mkdir -p models
fi

# Check if conversations directory exists
if [ ! -d "conversations" ]; then
    echo "📁 Creating conversations directory..."
    mkdir -p conversations
fi

# Start the application
cd backend
python start.py
