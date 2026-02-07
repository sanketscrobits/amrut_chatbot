from src.utils.vector_db.loader_strategies.base import DocumentLoaderStrategy
from pypdf import PdfReader
import os


class LocalLoader(DocumentLoaderStrategy):
    """
    PDF Document Loader with two modes:
    1. Fast Mode (PyPDF): 4-5 seconds, no OCR, no table extraction
    2. Accurate Mode (Docling): 30-40 seconds, OCR + table extraction
    
    Toggle via USE_FAST_PDF_PARSER environment variable.
    """
    
    def load_documents(self, path):
        # Check if PyPDF should be used (default: true for speed)
        use_fast_parser = os.getenv("USE_FAST_PDF_PARSER", "true").lower() == "true"
        
        if use_fast_parser:
            # Fast path: PyPDF (4-5 seconds)
            print(f"[LocalLoader] Using PyPDF for fast parsing: {path}")
            return self._load_with_pypdf(path)
        else:
            # Slow path: Docling (for complex PDFs with tables/images)
            print(f"[LocalLoader] Using Docling for accurate parsing: {path}")
            return self._load_with_docling(path)
    
    def _load_with_pypdf(self, path: str) -> str:
        """
        Fast PDF parsing using PyPDF.
        Best for text-heavy PDFs without complex tables.
        """
        try:
            reader = PdfReader(path)
            pages = []
            
            for page_num, page in enumerate(reader.pages, 1):
                text = page.extract_text()
                if text.strip():  # Only include non-empty pages
                    pages.append(f"--- Page {page_num} ---\n{text}")
            
            content = "\n\n".join(pages)
            print(f"[LocalLoader] PyPDF extracted {len(pages)} pages, {len(content)} chars")
            return content
            
        except Exception as e:
            print(f"[LocalLoader] PyPDF failed: {e}. Falling back to Docling...")
            return self._load_with_docling(path)
    
    def _load_with_docling(self, path: str) -> str:
        """
        Accurate PDF parsing using Docling.
        Supports OCR, table extraction, and complex layouts.
        """
        from docling.document_converter import DocumentConverter
        
        result = DocumentConverter().convert(path)
        document = result.document
        markdown_output = document.export_to_markdown()
        
        print(f"[LocalLoader] Docling extracted {len(markdown_output)} chars")
        return markdown_output


if __name__ == "__main__":
    # Test script
    import sys
    if len(sys.argv) > 1:
        loader = LocalLoader()
        content = loader.load_documents(path=sys.argv[1])
        print(f"\nExtracted {len(content)} characters")
        print(f"Preview:\n{content[:500]}...")
