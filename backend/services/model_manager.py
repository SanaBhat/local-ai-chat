import os
import asyncio
import json
from typing import List, Optional, Dict, Any, AsyncGenerator
from pathlib import Path
import glob
import subprocess
import threading
from datetime import datetime

class ModelManager:
    def __init__(self):
        self.models_dir = Path("../models")
        self.loaded_models = {}
        self.current_model = None
        self.current_model_name = None
        self.model_process = None
        
    async def initialize(self):
        """Initialize model manager"""
        print("📁 Initializing Model Manager...")
        
        # Create models directory if it doesn't exist
        self.models_dir.mkdir(exist_ok=True)
        
        # Check for local GGUF models
        available_models = self._discover_local_models()
        print(f"🔍 Found {len(available_models)} local models")
        
        # Try to load a default model if available
        if available_models:
            default_model = available_models[0]["filename"]
            await self.load_model(default_model)
    
    def _discover_local_models(self) -> List[Dict[str, Any]]:
        """Discover GGUF models in local directory"""
        models = []
        gguf_files = glob.glob(str(self.models_dir / "*.gguf"))
        
        for file_path in gguf_files:
            filename = Path(file_path).name
            file_size = os.path.getsize(file_path) / (1024 * 1024 * 1024)  # GB
            
            models.append({
                "filename": filename,
                "path": file_path,
                "size_gb": round(file_size, 2),
                "local": True,
                "description": self._infer_model_info(filename)
            })
        
        return models
    
    def _infer_model_info(self, filename: str) -> str:
        """Infer model information from filename"""
        name_lower = filename.lower()
        
        if "qwen" in name_lower:
            return "Qwen model - Alibaba's large language model"
        elif "deepseek" in name_lower:
            return "DeepSeek model - Advanced coding and reasoning model"
        elif "llama" in name_lower:
            return "Llama model - Meta's open-source LLM"
        elif "mistral" in name_lower:
            return "Mistral model - Efficient small language model"
        elif "phi" in name_lower:
            return "Phi model - Microsoft's compact LM"
        else:
            return "General purpose language model"
    
    async def get_available_models(self) -> List[Dict[str, Any]]:
        """Get list of available models"""
        return self._discover_local_models()
    
    async def load_model(self, model_name: str) -> bool:
        """Load a model using llama.cpp executable"""
        try:
            model_path = self.models_dir / model_name
            
            if not model_path.exists():
                print(f"❌ Model not found: {model_path}")
                return False
            
            # Stop currently loaded model
            if self.model_process:
                self.model_process.terminate()
                self.model_process = None
            
            print(f"🔄 Loading model: {model_name}")
            
            # Use llama.cpp for inference
            # You'll need to download llama.cpp from: https://github.com/ggerganov/llama.cpp
            # and compile the main executable
            llama_path = "./llama.cpp/main"  # Adjust path as needed
            
            if not os.path.exists(llama_path):
                # Fallback to using llama-cpp-python if available
                return await self._load_model_python(model_path)
            
            # Start llama.cpp process
            self.model_process = subprocess.Popen(
                [llama_path, "-m", str(model_path), "--ctx-size", "4096"],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            self.current_model_name = model_name
            self.current_model = model_path
            
            print(f"✅ Model loaded successfully: {model_name}")
            return True
            
        except Exception as e:
            print(f"❌ Error loading model: {e}")
            return False
    
    async def _load_model_python(self, model_path: Path) -> bool:
        """Load model using llama-cpp-python library"""
        try:
            from llama_cpp import Llama
            
            self.current_model = Llama(
                model_path=str(model_path),
                n_ctx=4096,
                n_threads=8,
                verbose=False
            )
            self.current_model_name = model_path.name
            print(f"✅ Model loaded via llama-cpp-python: {model_path.name}")
            return True
        except ImportError:
            print("❌ llama-cpp-python not installed. Please install it or provide llama.cpp executable.")
            return False
        except Exception as e:
            print(f"❌ Error loading model with llama-cpp-python: {e}")
            return False
    
    async def generate_response(
        self, 
        message: str, 
        conversation_id: Optional[str] = None,
        documents: List[str] = None,
        json_schema: Optional[Dict] = None,
        max_tokens: int = 2048
    ) -> Dict[str, Any]:
        """Generate response from the model"""
        try:
            # Build context from documents
            context = ""
            if documents:
                context = "\n".join([f"Document: {doc}" for doc in documents])
            
            prompt = self._build_prompt(context, message)
            
            if hasattr(self.current_model, 'create_chat_completion'):
                # Using llama-cpp-python
                response = self.current_model.create_chat_completion(
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=max_tokens,
                    temperature=0.7,
                    stop=["</s>", "###"],
                    stream=False
                )
                content = response['choices'][0]['message']['content']
            else:
                # Using llama.cpp executable
                content = await self._generate_with_process(prompt, max_tokens)
            
            return {
                "response": content,
                "conversation_id": conversation_id or str(uuid.uuid4()),
                "timestamp": datetime.now().isoformat(),
                "model": self.current_model_name,
                "tokens_used": len(content.split())  # Approximate
            }
            
        except Exception as e:
            return {
                "response": f"Error generating response: {str(e)}",
                "conversation_id": conversation_id,
                "timestamp": datetime.now().isoformat(),
                "error": True
            }
    
    async def _generate_with_process(self, prompt: str, max_tokens: int) -> str:
        """Generate response using llama.cpp process"""
        if not self.model_process:
            raise Exception("No model process available")
        
        # Send prompt to process
        self.model_process.stdin.write(prompt + "\n")
        self.model_process.stdin.flush()
        
        # Read response
        response_lines = []
        while True:
            line = self.model_process.stdout.readline().strip()
            if not line or line == "###":
                break
            response_lines.append(line)
            
            # Safety break
            if len(response_lines) > max_tokens:
                break
        
        return "\n".join(response_lines)
    
    async def stream_response(
        self, 
        message: str, 
        conversation_id: Optional[str] = None
    ) -> AsyncGenerator[str, None]:
        """Stream response tokens one by one"""
        prompt = self._build_prompt("", message)
        
        if hasattr(self.current_model, 'create_chat_completion'):
            # Streaming with llama-cpp-python
            response = self.current_model.create_chat_completion(
                messages=[{"role": "user", "content": prompt}],
                max_tokens=2048,
                temperature=0.7,
                stop=["</s>", "###"],
                stream=True
            )
            
            for chunk in response:
                if 'content' in chunk['choices'][0]['delta']:
                    yield chunk['choices'][0]['delta']['content']
        else:
            # Fallback non-streaming
            response = await self.generate_response(message, conversation_id)
            for word in response["response"].split():
                yield word + " "
                await asyncio.sleep(0.01)  # Simulate streaming
    
    def _build_prompt(self, context: str, message: str) -> str:
        """Build the prompt for the model"""
        if context:
            return f"""Context information:
{context}

User question: {message}

Please provide a helpful response based on the context and your knowledge:"""
        else:
            return f"User: {message}\nAssistant:"
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get information about currently loaded model"""
        if not self.current_model:
            return {}
        
        return {
            "context_size": getattr(self.current_model, 'n_ctx', 4096),
            "parameters": "Unknown",  # Would need model metadata
            "format": "GGUF"
        }