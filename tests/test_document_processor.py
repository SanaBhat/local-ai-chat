import pytest
from fastapi import UploadFile
from io import BytesIO
from backend.app.services.document_processor import DocumentProcessor

@pytest.fixture
def document_processor():
    return DocumentProcessor()

@pytest.mark.asyncio
async def test_text_file_processing(document_processor):
    """Test processing of text files"""
    content = b"Hello, this is a test text file."
    file = UploadFile(filename="test.txt", file=BytesIO(content))
    
    result = await document_processor.process_file(file)
    assert result == "Hello, this is a test text file."

@pytest.mark.asyncio
async def test_unsupported_format(document_processor):
    """Test handling of unsupported file formats"""
    content = b"test content"
    file = UploadFile(filename="test.unsupported", file=BytesIO(content))
    
    with pytest.raises(ValueError):
        await document_processor.process_file(file)
