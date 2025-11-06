import pytest
import asyncio
from pathlib import Path
from backend.app.services.model_manager import ModelManager

@pytest.fixture
def model_manager():
    return ModelManager()

@pytest.mark.asyncio
async def test_model_initialization(model_manager):
    """Test that model manager initializes correctly"""
    await model_manager.initialize()
    assert hasattr(model_manager, 'models_dir')
    assert isinstance(model_manager.models_dir, Path)

@pytest.mark.asyncio
async def test_model_discovery(model_manager):
    """Test model discovery functionality"""
    await model_manager.initialize()
    models = await model_manager.get_available_models()
    assert isinstance(models, list)

def test_prompt_building(model_manager):
    """Test prompt building functionality"""
    context = "Test context"
    message = "Test message"
    prompt = model_manager._build_prompt(context, message)
    
    assert context in prompt
    assert message in prompt
    assert "User:" in prompt or "Context information" in prompt
