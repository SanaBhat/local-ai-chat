#!/usr/bin/env python3
"""
Startup script for LocalAI Chat application
"""
import os
import sys
import webbrowser
import threading
import time
from pathlib import Path

def check_dependencies():
    """Check if required dependencies are installed"""
    try:
        import fastapi
        import uvicorn
        print("✅ All core dependencies found")
    except ImportError as e:
        print(f"❌ Missing dependency: {e}")
        print("Please install requirements: pip install -r requirements.txt")
        return False
    return True

def start_server():
    """Start the FastAPI server"""
    os.chdir(Path(__file__).parent)
    os.system("uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload")

def open_browser():
    """Open browser after server starts"""
    time.sleep(3)  # Wait for server to start
    webbrowser.open("http://localhost:8000")

def main():
    print("🚀 Starting LocalAI Chat...")
    print("📋 Checking dependencies...")
    
    if not check_dependencies():
        sys.exit(1)
    
    print("🌐 Starting web server...")
    print("📖 Open http://localhost:8000 in your browser")
    print("⏹️  Press Ctrl+C to stop the server")
    
    # Start browser in background
    browser_thread = threading.Thread(target=open_browser)
    browser_thread.daemon = True
    browser_thread.start()
    
    # Start server
    start_server()

if __name__ == "__main__":
    main()
