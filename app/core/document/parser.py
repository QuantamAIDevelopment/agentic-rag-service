"""Document parser for multiple formats."""

import PyPDF2
from docx import Document as DocxDocument
from pathlib import Path
from typing import List, Dict, Any
from app.models.document import DocumentFormat

class DocumentParser:
    @staticmethod
    def detect_format(filename: str) -> DocumentFormat:
        """Detect document format from filename."""
        suffix = Path(filename).suffix.lower()
        format_map = {
            '.pdf': DocumentFormat.PDF,
            '.docx': DocumentFormat.DOCX,
            '.txt': DocumentFormat.TXT,
            '.md': DocumentFormat.MD
        }
        return format_map.get(suffix, DocumentFormat.TXT)
        
    def parse_document(self, file_path: str) -> List[str]:
        """Parse document and return list of text lines."""
        format_type = self.detect_format(file_path)
        text = self.extract_text(file_path, format_type)
        lines = self.segment_lines(text)
        return [line['content'] for line in lines]
        
    def extract_text(self, file_path: str, format: DocumentFormat) -> str:
        """Extract raw text from document."""
        if format == DocumentFormat.PDF:
            return self._parse_pdf(file_path)
        elif format == DocumentFormat.DOCX:
            return self._parse_docx(file_path)
        else:
            return self._parse_text(file_path)
        
    def segment_lines(self, text: str) -> List[Dict[str, Any]]:
        """Segment text into lines with metadata."""
        lines = text.split('\n')
        return [
            {
                'content': line.strip(),
                'line_number': i + 1,
                'length': len(line.strip())
            }
            for i, line in enumerate(lines)
            if line.strip()
        ]
    
    def _parse_pdf(self, file_path: str) -> str:
        """Parse PDF document."""
        with open(file_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            return "\n".join(page.extract_text() for page in reader.pages)
    
    def _parse_docx(self, file_path: str) -> str:
        """Parse DOCX document."""
        doc = DocxDocument(file_path)
        return "\n".join(paragraph.text for paragraph in doc.paragraphs)
    
    def _parse_text(self, file_path: str) -> str:
        """Parse text document."""
        with open(file_path, 'r', encoding='utf-8') as file:
            return file.read()