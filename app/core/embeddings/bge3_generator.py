"""BGE-3 embedding generator with optimizations."""

from sentence_transformers import SentenceTransformer
import numpy as np
from typing import List
import torch
import gc

class BGE3Generator:
    def __init__(self):
        self.model_name = "BAAI/bge-large-en-v1.5"
        self.model = None
        self._device = "cuda" if torch.cuda.is_available() else "cpu"
        self._load_model()
        
    def _load_model(self):
        """Load model with optimized settings."""
        try:
            self.model = SentenceTransformer(
                self.model_name,
                device=self._device
            )
            if self._device == "cuda":
                self.model.half()  # Use half precision for GPU
        except Exception as e:
            print(f"Model loading error: {e}")
            self.model = SentenceTransformer(self.model_name)
        
    def generate_embeddings(self, texts: List[str], batch_size: int = 32) -> np.ndarray:
        """Generate embeddings with memory optimization."""
        try:
            if not texts:
                return np.array([])
                
            # Process in smaller batches to avoid memory issues
            all_embeddings = []
            for i in range(0, len(texts), batch_size):
                batch = texts[i:i + batch_size]
                embeddings = self.model.encode(
                    batch, 
                    normalize_embeddings=True, 
                    convert_to_numpy=True,
                    show_progress_bar=False
                )
                all_embeddings.append(embeddings)
                
                # Clear GPU cache if using CUDA
                if self._device == "cuda":
                    torch.cuda.empty_cache()
                    
            return np.vstack(all_embeddings) if all_embeddings else np.array([])
            
        except Exception as e:
            print(f"Batch embedding generation failed: {e}")
            # Fallback to individual processing
            return np.array([self.generate_single_embedding(text) for text in texts])
        
    def generate_single_embedding(self, text: str) -> np.ndarray:
        """Generate embedding for a single text with error handling."""
        try:
            if not text or not text.strip():
                return np.zeros(1024)
                
            embedding = self.model.encode(
                [text.strip()], 
                normalize_embeddings=True, 
                convert_to_numpy=True,
                show_progress_bar=False
            )[0]
            
            # Clear cache periodically
            if self._device == "cuda" and torch.cuda.is_available():
                torch.cuda.empty_cache()
                
            return embedding
            
        except Exception as e:
            print(f"Single embedding generation failed: {e}")
            return np.zeros(1024)  # Return zero vector as fallback
        
    def get_embedding_dimension(self) -> int:
        """Return embedding dimension (1024 for BGE-large)."""
        return 1024
        
    @property
    def device(self) -> str:
        """Return device (cpu/cuda)."""
        return self._device
        
    def cleanup(self):
        """Clean up resources."""
        if self._device == "cuda":
            torch.cuda.empty_cache()
        gc.collect()
    
    def get_memory_usage(self) -> dict:
        """Get current memory usage statistics."""
        if self._device == "cuda" and torch.cuda.is_available():
            return {
                "device": "cuda",
                "allocated": torch.cuda.memory_allocated() / 1024**2,  # MB
                "cached": torch.cuda.memory_reserved() / 1024**2,  # MB
                "max_allocated": torch.cuda.max_memory_allocated() / 1024**2  # MB
            }
        else:
            import psutil
            process = psutil.Process()
            return {
                "device": "cpu",
                "memory_mb": process.memory_info().rss / 1024**2,
                "memory_percent": process.memory_percent()
            }
    
    def optimize_memory(self):
        """Optimize memory usage."""
        if self._device == "cuda":
            torch.cuda.empty_cache()
            torch.cuda.synchronize()
        gc.collect()

bge3_generator = BGE3Generator()