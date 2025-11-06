import json
import uuid
from typing import List, Dict, Any, Optional
from datetime import datetime
from pathlib import Path

class ConversationManager:
    def __init__(self):
        self.conversations_dir = Path("conversations")
        self.conversations = {}
        
    async def initialize(self):
        """Initialize conversation manager"""
        self.conversations_dir.mkdir(exist_ok=True)
        await self._load_saved_conversations()
    
    async def _load_saved_conversations(self):
        """Load conversations from disk"""
        for file_path in self.conversations_dir.glob("*.json"):
            try:
                with open(file_path, 'r') as f:
                    conversation_data = json.load(f)
                self.conversations[conversation_data['id']] = conversation_data
            except Exception as e:
                print(f"Error loading conversation {file_path}: {e}")
    
    async def branch_conversation(self, conversation_id: str, branch_point: int) -> Dict[str, Any]:
        """Create a branch from existing conversation"""
        if conversation_id not in self.conversations:
            raise ValueError("Conversation not found")
        
        original = self.conversations[conversation_id]
        new_id = str(uuid.uuid4())
        
        # Create branched conversation
        branched_conv = {
            "id": new_id,
            "title": f"Branch of {original.get('title', 'Conversation')}",
            "created_at": datetime.now().isoformat(),
            "messages": original["messages"][:branch_point],
            "parent_id": conversation_id,
            "branch_point": branch_point
        }
        
        self.conversations[new_id] = branched_conv
        await self._save_conversation(branched_conv)
        
        return branched_conv
    
    async def get_all_conversations(self) -> List[Dict[str, Any]]:
        """Get all conversations"""
        return list(self.conversations.values())
    
    async def delete_conversation(self, conversation_id: str) -> bool:
        """Delete a conversation"""
        if conversation_id in self.conversations:
            del self.conversations[conversation_id]
            
            # Delete file
            file_path = self.conversations_dir / f"{conversation_id}.json"
            if file_path.exists():
                file_path.unlink()
            
            return True
        return False
    
    async def _save_conversation(self, conversation: Dict[str, Any]):
        """Save conversation to disk"""
        file_path = self.conversations_dir / f"{conversation['id']}.json"
        with open(file_path, 'w') as f:
            json.dump(conversation, f, indent=2)
