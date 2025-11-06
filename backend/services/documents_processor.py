import os
import PyPDF2
from PIL import Image
import pytesseract
from fastapi import UploadFile
import io
from typing import List, Dict, Any
import asyncio

class DocumentProcessor:
    def __init__(self):
        self.supported_formats = {
            'pdf': self._process_pdf,
            'txt': self._process_text,
            'png': self._process_image,
            'jpg': self._process_image,
            'jpeg': self._process_image
        }
    
    async def initialize(self):
        """Initialize document processor"""
        print("📄 Initializing Document Processor...")
        # Check if tesseract is available for OCR
        try:
            pytesseract.get_tesseract_version()
            print("✅ OCR support available")
        except:
            print("⚠️  OCR not available - install tesseract for image text extraction")
    
    async def process_file(self, file: UploadFile) -> str:
        """Process uploaded file and extract text"""
        file_extension = file.filename.split('.')[-1].lower()
        
        if file_extension not in self.supported_formats:
            raise ValueError(f"Unsupported file format: {file_extension}")
        
        # Read file content
        content = await file.read()
        
        # Process based on file type
        processor = self.supported_formats[file_extension]
        text_content = await processor(content)
        
        return text_content
    
    async def _process_pdf(self, content: bytes) -> str:
        """Extract text from PDF"""
        try:
            pdf_file = io.BytesIO(content)
            pdf_reader = PyPDF2.PdfReader(pdf_file)
            
            text = ""
            for page in pdf_reader.pages:
                text += page.extract_text() + "\n"
            
            return text.strip()
        except Exception as e:
            raise Exception(f"PDF processing error: {str(e)}")
    
    async def _process_text(self, content: bytes) -> str:
        """Extract text from plain text file"""
        return content.decode('utf-8')
    
    async def _process_image(self, content: bytes) -> str:
        """Extract text from image using OCR"""
        try:
            image = Image.open(io.BytesIO(content))
            text = pytesseract.image_to_string(image)
            return text.strip()
        except Exception as e:
            raise Exception(f"Image OCR error: {str(e)}")