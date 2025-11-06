from fastapi import FastAPI, UploadFile, File, HTTPException, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
import uvicorn
import json
import os
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime
import asyncio

from .models.chat_models import ChatRequest, ChatResponse, Conversation, BranchRequest
from .services.model_manager import ModelManager
from .services.document_processor import DocumentProcessor
from .services.conversation_manager import ConversationManager

app = FastAPI(title="LocalAI Chat", description="Completely offline AI chat application", version="1.0.0")

# Serve frontend files
app.mount("/static", StaticFiles(directory="frontend"), name="static")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services
model_manager = ModelManager()
document_processor = DocumentProcessor()
conversation_manager = ConversationManager()

@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    print("🚀 Starting LocalAI Chat Server...")
    await model_manager.initialize()
    await document_processor.initialize()
    print("✅ Services initialized successfully")

@app.get("/")
async def serve_frontend():
    """Serve the main frontend page"""
    with open("frontend/index.html", "r") as f:
        return f.read()

@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy", 
        "model_loaded": model_manager.current_model is not None,
        "offline": True
    }

@app.get("/api/models")
async def get_available_models():
    """Get list of available GGUF models"""
    return await model_manager.get_available_models()

@app.post("/api/models/load/{model_name}")
async def load_model(model_name: str):
    """Load a specific model"""
    success = await model_manager.load_model(model_name)
    if success:
        return {"status": "success", "message": f"Model {model_name} loaded successfully"}
    else:
        raise HTTPException(status_code=400, detail=f"Failed to load model {model_name}")

@app.get("/api/models/current")
async def get_current_model():
    """Get currently loaded model info"""
    if model_manager.current_model:
        return {
            "name": model_manager.current_model_name,
            "loaded": True,
            "info": model_manager.get_model_info()
        }
    return {"loaded": False}

@app.post("/api/chat")
async def chat(request: ChatRequest):
    """Main chat endpoint - completely offline"""
    try:
        response = await model_manager.generate_response(
            message=request.message,
            conversation_id=request.conversation_id,
            documents=request.documents,
            json_schema=request.json_schema,
            max_tokens=request.max_tokens
        )
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Chat error: {str(e)}")

@app.post("/api/upload")
async def upload_file(file: UploadFile = File(...)):
    """Upload and process documents offline"""
    try:
        content = await document_processor.process_file(file)
        return {
            "status": "success",
            "file_id": str(uuid.uuid4()),
            "filename": file.filename,
            "content_type": file.content_type,
            "content_preview": content[:200] + "..." if len(content) > 200 else content,
            "processed_at": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"File processing error: {str(e)}")

@app.post("/api/conversations/branch")
async def branch_conversation(request: BranchRequest):
    """Create a branch from existing conversation"""
    new_conversation = await conversation_manager.branch_conversation(
        request.conversation_id, 
        request.branch_point
    )
    return new_conversation

@app.get("/api/conversations")
async def get_conversations():
    """Get all conversations"""
    return await conversation_manager.get_all_conversations()

@app.delete("/api/conversations/{conversation_id}")
async def delete_conversation(conversation_id: str):
    """Delete a conversation"""
    success = await conversation_manager.delete_conversation(conversation_id)
    if success:
        return {"status": "success"}
    else:
        raise HTTPException(status_code=404, detail="Conversation not found")

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket for real-time chat streaming"""
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_text()
            message_data = json.loads(data)
            
            # Stream response chunks
            async for chunk in model_manager.stream_response(
                message=message_data["message"],
                conversation_id=message_data.get("conversation_id")
            ):
                await websocket.send_text(json.dumps({"chunk": chunk}))
                
    except Exception as e:
        print(f"WebSocket error: {e}")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
