"""Text chunking for better embedding storage."""

from typing import List
import re

class TextChunker:
    def __init__(self, chunk_size: int = 200, overlap: int = 50):
        self.chunk_size = chunk_size
        self.overlap = overlap
    
    def chunk_text(self, text: str) -> List[str]:
        """Split text into small overlapping chunks for better retrieval."""
        # Clean text
        text = re.sub(r'\s+', ' ', text.strip())
        
        # Split by sentences first
        sentences = re.split(r'[.!?]+', text)
        
        chunks = []
        current_chunk = ""
        
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue
                
            # If adding this sentence would exceed chunk size
            if len(current_chunk + " " + sentence) > self.chunk_size:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                    # Start new chunk with overlap
                    words = current_chunk.split()
                    if len(words) > self.overlap:
                        current_chunk = " ".join(words[-self.overlap:]) + " " + sentence
                    else:
                        current_chunk = sentence
                else:
                    # Single sentence is too long, split by words
                    words = sentence.split()
                    for i in range(0, len(words), self.chunk_size):
                        chunk_words = words[i:i + self.chunk_size]
                        chunks.append(" ".join(chunk_words))
                    current_chunk = ""
            else:
                current_chunk = (current_chunk + " " + sentence).strip()
        
        # Add final chunk
        if current_chunk:
            chunks.append(current_chunk.strip())
        
        return [chunk for chunk in chunks if len(chunk.strip()) > 20]  # Filter very short chunks

text_chunker = TextChunker(chunk_size=200, overlap=50)