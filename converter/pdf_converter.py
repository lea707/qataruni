import os
import pdfplumber
from .base import DocumentConverter

class PDFConverter(DocumentConverter):
    def load_document(self):
        if hasattr(self.input_path, 'read'):  # file-like object
            self.pdf = pdfplumber.open(self.input_path)
        elif isinstance(self.input_path, str):
            if not os.path.exists(self.input_path):
                raise FileNotFoundError(f"❌ File not found: {self.input_path}")
            if not self.input_path.lower().endswith('.pdf'):
                raise ValueError("❌ Only .pdf files are supported.")
            self.pdf = pdfplumber.open(self.input_path)
        else:
            raise TypeError("❌ input_path must be a file path or file-like object.")

    def convert_to_text(self):
        if not hasattr(self, 'pdf'):
            raise RuntimeError("⚠️ Document not loaded. Call load_document() first.")

        text_blocks = []
        for page in self.pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text_blocks.append(page_text.strip())

        self.text = "\n".join(text_blocks)