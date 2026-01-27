"""
Tests for document processing service.
"""
import pytest
import io
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.document_service import DocumentProcessor, PDF_SUPPORT, DOCX_SUPPORT


class TestDocumentProcessor:
    """Test cases for DocumentProcessor class."""

    def test_text_file_extraction(self):
        """Test extraction from plain text files."""
        content = b"Hello, this is a test document.\nIt has multiple lines.\nThird line here."
        filename = "test.txt"

        result = DocumentProcessor.process_document(filename, content)

        assert result['success'] is True
        assert "Hello, this is a test document" in result['text_content']
        assert result['metadata']['extraction']['extraction_method'] == 'utf-8_decode'
        print("✅ Text file extraction: PASSED")

    def test_markdown_file_extraction(self):
        """Test extraction from markdown files."""
        content = b"# Heading\n\nThis is **bold** text.\n\n- Item 1\n- Item 2"
        filename = "test.md"

        result = DocumentProcessor.process_document(filename, content)

        assert result['success'] is True
        assert "# Heading" in result['text_content']
        assert "**bold**" in result['text_content']
        print("✅ Markdown file extraction: PASSED")

    def test_file_size_validation(self):
        """Test that oversized files are rejected."""
        # Create content larger than MAX_FILE_SIZE (10MB)
        content = b"x" * (11 * 1024 * 1024)  # 11MB
        filename = "large.txt"

        result = DocumentProcessor.process_document(filename, content)

        assert result['success'] is False
        assert "exceeds maximum" in result['error']
        print("✅ File size validation: PASSED")

    def test_invalid_extension(self):
        """Test that invalid file extensions are rejected."""
        content = b"Some content"
        filename = "test.exe"

        result = DocumentProcessor.process_document(filename, content)

        assert result['success'] is False
        assert "not allowed" in result['error']
        print("✅ Invalid extension validation: PASSED")

    def test_content_truncation(self):
        """Test that long content is truncated."""
        # Create content longer than MAX_CONTENT_LENGTH (50000)
        content = ("x" * 60000).encode('utf-8')
        filename = "long.txt"

        result = DocumentProcessor.process_document(filename, content)

        assert result['success'] is True
        assert len(result['text_content']) == DocumentProcessor.MAX_CONTENT_LENGTH
        assert result['metadata']['extraction']['truncated'] is True
        print("✅ Content truncation: PASSED")

    def test_format_document_for_llm(self):
        """Test LLM prompt formatting."""
        user_message = "Summarize this document"
        document_content = "This is the document content."
        filename = "test.txt"

        formatted = DocumentProcessor.format_document_for_llm(
            user_message, document_content, filename
        )

        assert "Summarize this document" in formatted
        assert "Document Content (File: test.txt)" in formatted
        assert "This is the document content." in formatted
        print("✅ LLM format: PASSED")

    @pytest.mark.skipif(not PDF_SUPPORT, reason="pypdf not installed")
    def test_pdf_extraction(self):
        """Test extraction from PDF files."""
        from pypdf import PdfWriter

        # Create a simple PDF in memory
        writer = PdfWriter()
        page = writer.add_blank_page(width=612, height=792)

        # Add text to the PDF using annotations (simple approach)
        # Note: For a real test, we'd use a pre-made PDF or reportlab
        pdf_buffer = io.BytesIO()
        writer.write(pdf_buffer)
        pdf_content = pdf_buffer.getvalue()

        filename = "test.pdf"
        result = DocumentProcessor.process_document(filename, pdf_content)

        assert result['success'] is True
        assert 'page_count' in result['metadata']['extraction']
        print(f"✅ PDF extraction: PASSED (method: {result['metadata']['extraction']['extraction_method']})")

    @pytest.mark.skipif(not DOCX_SUPPORT, reason="python-docx not installed")
    def test_docx_extraction(self):
        """Test extraction from DOCX files."""
        from docx import Document

        # Create a simple DOCX in memory
        doc = Document()
        doc.add_heading('Test Document', 0)
        doc.add_paragraph('This is a test paragraph.')
        doc.add_paragraph('Second paragraph with more content.')

        # Add a simple table
        table = doc.add_table(rows=2, cols=2)
        table.cell(0, 0).text = 'Header 1'
        table.cell(0, 1).text = 'Header 2'
        table.cell(1, 0).text = 'Data 1'
        table.cell(1, 1).text = 'Data 2'

        docx_buffer = io.BytesIO()
        doc.save(docx_buffer)
        docx_content = docx_buffer.getvalue()

        filename = "test.docx"
        result = DocumentProcessor.process_document(filename, docx_content)

        assert result['success'] is True
        assert 'Test Document' in result['text_content']
        assert 'test paragraph' in result['text_content']
        assert result['metadata']['extraction']['extraction_method'] == 'python-docx'
        print(f"✅ DOCX extraction: PASSED")
        print(f"   Paragraphs: {result['metadata']['extraction'].get('paragraph_count', 'N/A')}")
        print(f"   Tables: {result['metadata']['extraction'].get('table_count', 0)}")

    def test_get_supported_formats(self):
        """Test that supported formats are correctly reported."""
        formats = DocumentProcessor.get_supported_formats()

        assert '.txt' in formats
        assert '.md' in formats
        assert '.pdf' in formats
        assert '.docx' in formats
        print("✅ Supported formats: PASSED")
        print(f"   Formats: {formats}")


def run_all_tests():
    """Run all tests manually."""
    print("\n" + "=" * 60)
    print("Document Service Tests")
    print("=" * 60)
    print(f"\nPDF Support: {'✅ Available' if PDF_SUPPORT else '❌ Not installed'}")
    print(f"DOCX Support: {'✅ Available' if DOCX_SUPPORT else '❌ Not installed'}\n")

    test_instance = TestDocumentProcessor()
    tests = [
        ("Text file extraction", test_instance.test_text_file_extraction),
        ("Markdown file extraction", test_instance.test_markdown_file_extraction),
        ("File size validation", test_instance.test_file_size_validation),
        ("Invalid extension validation", test_instance.test_invalid_extension),
        ("Content truncation", test_instance.test_content_truncation),
        ("LLM format", test_instance.test_format_document_for_llm),
        ("Supported formats", test_instance.test_get_supported_formats),
    ]

    if PDF_SUPPORT:
        tests.append(("PDF extraction", test_instance.test_pdf_extraction))
    if DOCX_SUPPORT:
        tests.append(("DOCX extraction", test_instance.test_docx_extraction))

    passed = 0
    failed = 0

    for name, test_func in tests:
        try:
            test_func()
            passed += 1
        except Exception as e:
            print(f"❌ {name}: FAILED - {e}")
            failed += 1

    print("\n" + "=" * 60)
    print(f"Results: {passed} passed, {failed} failed")
    print("=" * 60)

    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
