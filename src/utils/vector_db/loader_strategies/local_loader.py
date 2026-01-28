from src.utils.vector_db.loader_strategies.base import DocumentLoaderStrategy
from docling.document_converter import DocumentConverter


class LocalLoader(DocumentLoaderStrategy):
    def load_documents(self, path):
        result = DocumentConverter().convert(path)
        document = result.document
        markdown_output = document.export_to_markdown()
        return markdown_output

if __name__ == "__main__":
    loader = LocalLoader()
    loader.load_documents(path="F:\ScroBits_Tech\scrobits-ai-poc-mirems\POC\Pinecone\documents\Story1.pdf")
