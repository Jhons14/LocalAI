"""
Document processing service for handling uploaded files.
"""
import os
import tempfile
from typing import Dict, Any, Optional, Tuple
from pathlib import Path
import logging
import mimetypes

logger = logging.getLogger(__name__)

class DocumentProcessor:
    """Service for processing uploaded documents and extracting text content."""
    
    ALLOWED_EXTENSIONS = {'.txt', '.md', '.pdf', '.docx'}
    ALLOWED_MIME_TYPES = {
        'text/plain',
        'text/markdown', 
        'application/pdf',
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
    }
    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
    MAX_CONTENT_LENGTH = 50000  # Maximum characters to include in prompt
    
    @classmethod
    def validate_file(cls, filename: str, content: bytes) -> Dict[str, Any]:
        """Validate file type, size, and basic security checks."""
        validation_result = {
            'valid': False,
            'error': None,
            'file_info': {}
        }
        
        try:
            # Check file size
            file_size = len(content)
            if file_size > cls.MAX_FILE_SIZE:
                validation_result['error'] = f"File size ({file_size / 1024 / 1024:.1f}MB) exceeds maximum ({cls.MAX_FILE_SIZE / 1024 / 1024}MB)"
                return validation_result
            
            # Check file extension
            file_extension = Path(filename).suffix.lower()
            if file_extension not in cls.ALLOWED_EXTENSIONS:
                validation_result['error'] = f"File extension '{file_extension}' not allowed. Supported: {', '.join(cls.ALLOWED_EXTENSIONS)}"
                return validation_result
            
            # Check MIME type (basic check)
            mime_type, _ = mimetypes.guess_type(filename)
            if mime_type and mime_type not in cls.ALLOWED_MIME_TYPES:
                validation_result['error'] = f"MIME type '{mime_type}' not allowed"
                return validation_result
            
            # Basic security check - look for suspicious content in first 1000 bytes
            sample = content[:1000].decode('utf-8', errors='ignore').lower()
            suspicious_patterns = ['<script', '<?php', 'eval(', 'exec(', 'system(']
            for pattern in suspicious_patterns:
                if pattern in sample:
                    validation_result['error'] = f"Potentially malicious content detected"
                    return validation_result
            
            validation_result['valid'] = True
            validation_result['file_info'] = {
                'filename': filename,
                'size': file_size,
                'extension': file_extension,
                'mime_type': mime_type
            }
            
        except Exception as e:
            validation_result['error'] = f"File validation error: {str(e)}"
            
        return validation_result
    
    @classmethod
    def extract_text_content(cls, filename: str, content: bytes) -> Tuple[str, Dict[str, Any]]:
        """Extract text content from various file types."""
        try:
            file_extension = Path(filename).suffix.lower()
            extracted_text = ""
            metadata = {
                'extraction_method': 'unknown',
                'char_count': 0,
                'truncated': False
            }
            
            if file_extension in ['.txt', '.md']:
                # Handle text files
                try:
                    extracted_text = content.decode('utf-8')
                    metadata['extraction_method'] = 'utf-8_decode'
                except UnicodeDecodeError:
                    try:
                        extracted_text = content.decode('latin-1')
                        metadata['extraction_method'] = 'latin-1_decode'
                    except UnicodeDecodeError:
                        extracted_text = content.decode('utf-8', errors='ignore')
                        metadata['extraction_method'] = 'utf-8_decode_ignore_errors'
                        
            elif file_extension == '.pdf':
                # For PDF files, we'd need PyPDF2 or similar
                # For now, return a placeholder - this would need proper PDF processing
                extracted_text = "[PDF content processing not yet implemented - please use text files for now]"
                metadata['extraction_method'] = 'pdf_placeholder'
                
            elif file_extension == '.docx':
                # For DOCX files, we'd need python-docx
                # For now, return a placeholder - this would need proper DOCX processing
                extracted_text = "[DOCX content processing not yet implemented - please use text files for now]"
                metadata['extraction_method'] = 'docx_placeholder'
                
            else:
                raise ValueError(f"Unsupported file type: {file_extension}")
            
            # Truncate content if too long
            original_length = len(extracted_text)
            if original_length > cls.MAX_CONTENT_LENGTH:
                extracted_text = extracted_text[:cls.MAX_CONTENT_LENGTH]
                metadata['truncated'] = True
                metadata['original_length'] = original_length
            
            metadata['char_count'] = len(extracted_text)
            
            return extracted_text, metadata
            
        except Exception as e:
            logger.error(f"Error extracting text from {filename}: {str(e)}")
            raise ValueError(f"Failed to extract text content: {str(e)}")
    
    @classmethod
    def process_document(cls, filename: str, content: bytes) -> Dict[str, Any]:
        """Complete document processing pipeline."""
        result = {
            'success': False,
            'text_content': '',
            'metadata': {},
            'error': None
        }
        
        try:
            # Validate file
            validation = cls.validate_file(filename, content)
            if not validation['valid']:
                result['error'] = validation['error']
                return result
            
            # Extract text content
            text_content, extraction_metadata = cls.extract_text_content(filename, content)
            
            result.update({
                'success': True,
                'text_content': text_content,
                'metadata': {
                    'file_info': validation['file_info'],
                    'extraction': extraction_metadata,
                    'processing_timestamp': None  # Could add timestamp if needed
                }
            })
            
        except Exception as e:
            result['error'] = str(e)
            logger.error(f"Document processing failed for {filename}: {str(e)}")
            
        return result
    
    @classmethod
    def format_document_for_llm(cls, user_message: str, document_content: str, filename: str) -> str:
        """Format the user message and document content for optimal LLM processing."""
        if not document_content.strip():
            return user_message
            
        formatted_prompt = f"""{user_message}

--- Document Content (File: {filename}) ---
{document_content.strip()}
--- End of Document ---

Please analyze the above document content in the context of my request."""
        
        return formatted_prompt
    
    @classmethod
    def get_supported_formats(cls) -> Dict[str, str]:
        """Get list of supported file formats with descriptions."""
        return {
            '.txt': 'Plain text files',
            '.md': 'Markdown files', 
            '.pdf': 'PDF documents (basic support)',
            '.docx': 'Microsoft Word documents (basic support)'
        }