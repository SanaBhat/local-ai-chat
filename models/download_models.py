#!/usr/bin/env python3
"""
Script to download GGUF models for offline use
"""
import os
import requests
import urllib.request
from pathlib import Path
import sys

def download_file(url, filename):
    """Download a file with progress bar"""
    def progress_hook(count, block_size, total_size):
        percent = int(count * block_size * 100 / total_size)
        print(f"\rDownloading {filename}: {percent}%", end='', flush=True)
    
    urllib.request.urlretrieve(url, filename, progress_hook)
    print()  # New line after download

def main():
    models_dir = Path("models")
    models_dir.mkdir(exist_ok=True)
    
    # List of recommended small models for testing
    models = [
        {
            "name": "TinyLlama 1.1B",
            "url": "https://huggingface.co/TheBloke/TinyLlama-1.1B-Chat-v1.0-GGUF/resolve/main/tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf",
            "filename": "tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf",
            "size": "0.8GB"
        },
        {
            "name": "Phi-2 3B",
            "url": "https://huggingface.co/TheBloke/phi-2-GGUF/resolve/main/phi-2.q4_K_M.gguf",
            "filename": "phi-2.q4_K_M.gguf", 
            "size": "1.8GB"
        }
    ]
    
    print("🔍 Available models for download:")
    for i, model in enumerate(models, 1):
        print(f"{i}. {model['name']} ({model['size']}) - {model['filename']}")
    
    choice = input("\nEnter model number to download (or 'a' for all): ").strip()
    
    if choice.lower() == 'a':
        # Download all models
        for model in models:
            download_model(model, models_dir)
    elif choice.isdigit() and 1 <= int(choice) <= len(models):
        # Download selected model
        download_model(models[int(choice) - 1], models_dir)
    else:
        print("Invalid choice")

def download_model(model, models_dir):
    """Download a single model"""
    file_path = models_dir / model["filename"]
    
    if file_path.exists():
        print(f"✅ {model['name']} already exists")
        return
    
    print(f"⬇️  Downloading {model['name']}...")
    try:
        download_file(model["url"], file_path)
        print(f"✅ Successfully downloaded {model['filename']}")
    except Exception as e:
        print(f"❌ Error downloading {model['name']}: {e}")

if __name__ == "__main__":
    main()
