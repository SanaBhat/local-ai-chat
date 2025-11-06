# LocalAI Chat - 100% Offline AI Assistant

Proof of Concept for a completely offline ChatGPT-like application that runs entirely on your laptop without any internet connection or external APIs.

## Features

- ✅ **100% Offline** - No internet required after setup
- ✅ **200,000+ GGUF Model Support** - Compatible with most GGUF format models
- ✅ **Document Processing** - Upload and chat with PDFs, images, text files
- ✅ **Conversation Branching** - Create branches from any point in conversations
- ✅ **JSON Schema Support** - Constrain AI responses to specific formats
- ✅ **Math & Code Rendering** - Proper formatting for technical content
- ✅ **Modern Web UI** - Clean, responsive interface

## Quick Start
## Quick Start
### 1. Installation

```bash
# Clone the repository
git clone <repository-url>
cd local-ai-chat

# Install backend dependencies
cd backend
pip install -r requirements.txt

# Download some models
cd ../models
python download_models.py
```

### 2. Start the Application
```bash
cd backend
python start.py
```

The application will automatically open in your browser at http://localhost:8000


