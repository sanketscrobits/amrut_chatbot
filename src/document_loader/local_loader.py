import os
import re
from pathlib import Path
from pypdf import PdfReader
from llama_index.core import SimpleDirectoryReader

class DocumentLoader:
    """Document loader that properly extracts text from PDFs and other file types."""
    
    def __init__(self, documents_dir: str = "documents"):
        """Initialize loader with documents directory path."""
        self.project_root = Path(__file__).resolve().parent.parent.parent
        self.documents_dir = self.project_root / documents_dir
    
    def _extract_pdf_text(self, pdf_path: Path) -> str:
        """Extract text from PDF using pypdf."""
        try:
            reader = PdfReader(str(pdf_path))
            full_text = ""
            
            for page in reader.pages:
                page_text = page.extract_text()
                if page_text:
                    full_text += page_text + " "
            
            # Clean up text
            full_text = re.sub(r'\n+', ' ', full_text)
            full_text = re.sub(r'\s+', ' ', full_text)
            return full_text.strip()
            
        except Exception as e:
            print(f"Error extracting PDF {pdf_path.name}: {e}")
            return ""
    
    def _extract_other_text(self, file_path: Path) -> str:
        """Extract text from non-PDF files using LlamaIndex."""
        try:
            reader = SimpleDirectoryReader(
                input_files=[str(file_path)],
                required_exts=[".txt", ".md", ".docx"]
            )
            documents = reader.load_data()
            
            if documents:
                return documents[0].text.strip()
            return ""
            
        except Exception as e:
            print(f"Error extracting {file_path.name}: {e}")
            return ""
    
    def load_and_combine_text(self) -> str:
        """
        Load all documents from the folder and return combined text.
        
        Returns:
            Combined text from all documents with separators
        """
        if not self.documents_dir.exists():
            return f"Documents directory not found: {self.documents_dir}"
        
        combined_parts = []
        processed_files = 0
        
        # Process all files in the directory
        for file_path in self.documents_dir.iterdir():
            if file_path.is_file():
                processed_files += 1
                
                # Extract text based on file type
                if file_path.suffix.lower() == '.pdf':
                    doc_text = self._extract_pdf_text(file_path)
                else:
                    doc_text = self._extract_other_text(file_path)
                
                if doc_text:
                    # Add document separator
                    separator = f"\n\n--- {file_path.name} ---\n"
                    combined_parts.extend([separator, doc_text])
        
        if not combined_parts:
            return "No readable content found in documents."
        
        combined_text = "".join(combined_parts)
        print(f"Processed {processed_files} files, total characters: {len(combined_text)}")
        
        return combined_text

# Convenience function
def get_combined_text(documents_dir: str = "documents") -> str:
    """Get combined text from all documents in the folder."""
    loader = DocumentLoader(documents_dir)
    return loader.load_and_combine_text()

# Example usage
if __name__ == "__main__":
    # Get combined text from all documents
    combined_text = get_combined_text()
    print(f"Combined text preview:\n{combined_text[:5000]}...")