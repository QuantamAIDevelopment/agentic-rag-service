"""Document upload endpoint."""

from fastapi import APIRouter, UploadFile, File
from typing import List
from app.config.settings import settings
from app.models.document import DocumentUploadResponse, DocumentStatus

router = APIRouter(prefix="/upload", tags=["upload"])

@router.post("/documents", response_model=List[DocumentUploadResponse])
async def upload_documents(files: List[UploadFile] = File(...)):
    """Process every line of every document into single vector store."""
    from app.core.vector_store.store_manager import store_manager
    from app.core.embeddings.bge3_generator import bge3_generator
    from app.core.document.pdf_extractor import pdf_extractor
    
    # Initialize single document store
    await store_manager.initialize_all_stores()
    store = store_manager.get_store("documents")
    
    results = []
    total_lines_processed = 0
    
    for file in files:
        try:
            print(f"\n{'='*60}")
            print(f"PROCESSING: {file.filename}")
            print(f"{'='*60}")
            
            # Check if document already exists
            if await store.check_document_exists(file.filename):
                print(f"SKIPPED: {file.filename} - Document already exists")
                results.append(DocumentUploadResponse(
                    document_id=f"doc_{len(results)+1}",
                    filename=file.filename,
                    status=DocumentStatus.COMPLETED,
                    message="Document already exists - skipped duplicate"
                ))
                continue
            
            # Read file content
            content = await file.read()
            file_lines_processed = 0
            
            if file.filename.lower().endswith('.pdf'):
                # Extract complete text from PDF
                print("Extracting text from PDF...")
                text_content = pdf_extractor.extract_text_from_bytes(content)
                
                if "Error extracting PDF" in text_content:
                    raise Exception(f"PDF extraction failed: {text_content}")
                
                # Extract every line
                lines = pdf_extractor.extract_lines(text_content)
                print(f"Extracted {len(lines)} lines from PDF")
                
                if not lines:
                    raise Exception("No text content found in PDF")
                
                # Process lines in optimized batches
                embeddings_data = []
                batch_size = settings.BATCH_SIZE_UPLOAD  # Use configurable batch size
                
                for i, line in enumerate(lines, 1):
                    line = line.strip()
                    if len(line) > 10:  # Process all meaningful lines
                        try:
                            # Generate embedding for this line
                            embedding = bge3_generator.generate_single_embedding(line)
                            
                            embeddings_data.append({
                                'content': line,
                                'embedding': embedding,
                                'metadata': {
                                    'filename': file.filename,
                                    'line_number': i,
                                    'type': 'document_line',
                                    'document_type': 'pdf'
                                }
                            })
                            
                            file_lines_processed += 1
                            
                            # Store in larger batches for better performance
                            if len(embeddings_data) >= batch_size:
                                await store.insert_embeddings(embeddings_data)
                                print(f"  Batch stored: {file_lines_processed} lines processed")
                                embeddings_data = []
                                
                        except Exception as e:
                            print(f"  Error on line {i}: {str(e)}")
                            continue  # Continue processing other lines
                
                # Store remaining lines
                if embeddings_data:
                    await store.insert_embeddings(embeddings_data)
                
            elif file.filename.lower().endswith(('.txt', '.md')):
                # Process text files
                print("Processing text file...")
                text_content = content.decode('utf-8')
                lines = text_content.split('\n')
                
                embeddings_data = []
                
                for i, line in enumerate(lines, 1):
                    line = line.strip()
                    if len(line) > 10:
                        embedding = bge3_generator.generate_single_embedding(line)
                        embeddings_data.append({
                            'content': line,
                            'embedding': embedding,
                            'metadata': {
                                'filename': file.filename,
                                'line_number': i,
                                'type': 'document_line',
                                'document_type': 'text'
                            }
                        })
                        file_lines_processed += 1
                
                if embeddings_data:
                    await store.insert_embeddings(embeddings_data)
            
            else:
                raise Exception(f"Unsupported file type: {file.filename}")
            
            total_lines_processed += file_lines_processed
            
            print(f"SUCCESS: {file.filename}")
            print(f"Lines processed: {file_lines_processed}")
            print(f"Total lines so far: {total_lines_processed}")
            
            results.append(DocumentUploadResponse(
                document_id=f"doc_{len(results)+1}",
                filename=file.filename,
                status=DocumentStatus.COMPLETED,
                message=f"Processed {file_lines_processed} lines into documents store"
            ))
            
        except Exception as e:
            print(f"FAILED: {file.filename} - {str(e)}")
            results.append(DocumentUploadResponse(
                document_id=f"doc_{len(results)+1}",
                filename=file.filename,
                status=DocumentStatus.FAILED,
                message=f"Processing failed: {str(e)}"
            ))
    
    print(f"\n{'='*60}")
    print(f"UPLOAD COMPLETE")
    print(f"Total files: {len(files)}")
    print(f"Total lines processed: {total_lines_processed}")
    print(f"{'='*60}")
    
    return results