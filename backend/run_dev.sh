#!/bin/bash

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install/update requirements
echo "Installing requirements..."
pip install -q -r requirements.txt

# Run the development server
echo "Starting YTT backend on http://localhost:8000"
echo "API docs available at http://localhost:8000/docs"
echo ""
uvicorn main:app --reload --host 127.0.0.1 --port 8000