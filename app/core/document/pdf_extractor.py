"""Enhanced PDF text extraction for complete document processing."""

import PyPDF2
import pdfplumber
import io
import warnings
import logging
import sys
from typing import List

# Complete warning suppression
warnings.filterwarnings("ignore")
logging.getLogger().setLevel(logging.ERROR)
logging.getLogger("pdfplumber").setLevel(logging.CRITICAL)
logging.getLogger("PyPDF2").setLevel(logging.CRITICAL)

# Redirect stderr temporarily during PDF processing
class SuppressOutput:
    def __enter__(self):
        self._original_stderr = sys.stderr
        sys.stderr = open('nul' if sys.platform == 'win32' else '/dev/null', 'w')
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        sys.stderr.close()
        sys.stderr = self._original_stderr
try:
    import pytesseract
    from PIL import Image
    OCR_AVAILABLE = True
except ImportError:
    OCR_AVAILABLE = False
    print("OCR not available. Install pytesseract and Pillow for image text extraction.")

try:
    import camelot
    import warnings
    warnings.filterwarnings("ignore", category=UserWarning, module="camelot")
    CAMELOT_AVAILABLE = True
except ImportError:
    CAMELOT_AVAILABLE = False
    print("Camelot not available. Install camelot-py for advanced table extraction.")

class PDFExtractor:
    def extract_text_from_bytes(self, pdf_bytes: bytes) -> str:
        """Optimized PDF extraction - fast processing with table/OCR support."""
        full_text = ""
        
        try:
            pdf_file = io.BytesIO(pdf_bytes)
            
            with SuppressOutput(), pdfplumber.open(pdf_file) as pdf:
                for page_num, page in enumerate(pdf.pages):
                    page_text = f"\n--- Page {page_num + 1} ---\n"
                    content_found = False
                    
                    # Step 1: Enhanced text extraction with multiple methods
                    text = page.extract_text(layout=True, x_tolerance=3, y_tolerance=3)
                    if not text or len(text.strip()) < 10:
                        text = page.extract_text()  # Fallback to basic extraction
                    
                    if text and text.strip() and len(text.strip()) > 5:
                        page_text += text + "\n"
                        content_found = True
                        print(f"Page {page_num + 1}: Text content extracted")
                    
                    # Step 2: Enhanced table extraction with multiple strategies
                    try:
                        # Strategy 1: Standard table extraction
                        tables = page.extract_tables(table_settings={
                            "vertical_strategy": "lines_strict",
                            "horizontal_strategy": "lines_strict",
                            "snap_tolerance": 3,
                            "join_tolerance": 3
                        })
                        
                        if not tables:
                            # Strategy 2: Text-based table detection
                            tables = page.extract_tables(table_settings={
                                "vertical_strategy": "text",
                                "horizontal_strategy": "text"
                            })
                        
                        if tables:
                            for table in tables:
                                for row in table:
                                    if row and any(cell for cell in row if cell):
                                        row_text = " | ".join(str(cell or "").strip() for cell in row)
                                        if row_text.strip():
                                            page_text += row_text + "\n"
                            content_found = True
                            print(f"Page {page_num + 1}: Table content extracted")
                    except Exception:
                        pass
                    
                    # Step 3: Enhanced OCR with multiple configurations
                    if OCR_AVAILABLE and (not content_found or len(page_text.strip()) < 50):
                        try:
                            # High resolution for better text recognition
                            page_image = page.to_image(resolution=300)
                            
                            # Multiple OCR strategies
                            ocr_configs = [
                                '--psm 6 -c tessedit_do_invert=0',  # Uniform text block
                                '--psm 4 -c tessedit_do_invert=0',  # Single column
                                '--psm 3 -c tessedit_do_invert=0',  # Fully automatic
                                '--psm 11 -c tessedit_do_invert=0'  # Sparse text
                            ]
                            
                            best_ocr_text = ""
                            for config in ocr_configs:
                                try:
                                    ocr_text = pytesseract.image_to_string(page_image.original, config=config)
                                    if len(ocr_text.strip()) > len(best_ocr_text.strip()):
                                        best_ocr_text = ocr_text
                                except Exception:
                                    continue
                            
                            if best_ocr_text and best_ocr_text.strip() and len(best_ocr_text.strip()) > 10:
                                page_text += best_ocr_text + "\n"
                                content_found = True
                                print(f"Page {page_num + 1}: OCR content extracted")
                        except Exception:
                            pass
                    
                    if content_found:
                        full_text += page_text
                    else:
                        print(f"Page {page_num + 1}: No extractable content found")
            
            if full_text.strip():
                return full_text
                
        except Exception as e:
            print(f"Enhanced pdfplumber failed: {e}, trying PyPDF2")
        
        # Enhanced PyPDF2 fallback with better text extraction
        try:
            pdf_file = io.BytesIO(pdf_bytes)
            with SuppressOutput(), warnings.catch_warnings():
                warnings.simplefilter("ignore")
                pdf_reader = PyPDF2.PdfReader(pdf_file)
            
            for page_num in range(len(pdf_reader.pages)):
                page = pdf_reader.pages[page_num]
                
                # Multiple extraction methods
                text = page.extract_text()
                if not text or len(text.strip()) < 10:
                    # Try alternative extraction
                    try:
                        text = ""
                        if '/Contents' in page:
                            content = page['/Contents']
                            if hasattr(content, 'get_data'):
                                raw_text = content.get_data().decode('utf-8', errors='ignore')
                                # Basic text extraction from raw content
                                import re
                                text_matches = re.findall(r'\((.*?)\)', raw_text)
                                text = ' '.join(text_matches)
                    except Exception:
                        pass
                
                if text and text.strip():
                    full_text += f"\n--- Page {page_num + 1} ---\n{text}\n"
            
            return full_text if full_text.strip() else "No extractable content found in PDF"
            
        except Exception as e:
            return f"Error extracting PDF: {str(e)}"
    
    def extract_lines(self, text: str) -> List[str]:
        """Extract every meaningful line from text."""
        lines = []
        for line in text.split('\n'):
            line = line.strip()
            # More aggressive line extraction
            if line and len(line) > 2:  # Even shorter lines
                # Clean up artifacts but preserve structure
                line = line.replace('\t', ' ').strip()
                # Remove page markers but keep other content
                if line and not line.startswith('--- Page') and not line.startswith('---'):
                    lines.append(line)
        return lines
    
    def extract_with_camelot(self, pdf_bytes: bytes) -> str:
        """Extract tables using Camelot for better table handling."""
        if not CAMELOT_AVAILABLE:
            return ""
        
        import tempfile
        import os
        tmp_path = None
        
        try:
            # Save bytes to temp file for Camelot
            with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp:
                tmp.write(pdf_bytes)
                tmp_path = tmp.name
            
            # Extract tables
            tables = camelot.read_pdf(tmp_path, pages='all')
            table_text = ""
            
            for i, table in enumerate(tables):
                table_text += f"\n[Camelot Table {i+1}]\n"
                df = table.df
                for _, row in df.iterrows():
                    row_text = " | ".join(str(cell).strip() for cell in row if str(cell).strip())
                    if row_text:
                        table_text += row_text + "\n"
            
            return table_text
            
        except Exception:
            return ""  # Suppress Camelot errors
        finally:
            # Clean up temp file with better error handling
            if tmp_path and os.path.exists(tmp_path):
                try:
                    os.unlink(tmp_path)
                except (PermissionError, OSError):
                    # File will be cleaned up by system temp cleanup
                    pass

pdf_extractor = PDFExtractor()