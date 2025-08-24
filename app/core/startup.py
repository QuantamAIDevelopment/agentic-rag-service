"""Application startup handler for automatic vector store initialization."""

import asyncio
from app.core.vector_store.store_manager import store_manager

async def initialize_vector_stores():
    """Initialize all vector stores with retry logic."""
    max_retries = 3
    retry_delay = 5
    
    for attempt in range(max_retries):
        try:
            await store_manager.initialize_all_stores()
            print("✓ All vector stores initialized successfully")
            
            # Initialize chat memory tables
            # from app.core.memory.chat_memory import chat_memory  # Commented out
            # await chat_memory.create_tables()  # Commented out
            # print("✓ Chat memory tables initialized")  # Commented out
            
            return True
        except Exception as e:
            print(f"Attempt {attempt + 1}/{max_retries} failed: {e}")
            if attempt < max_retries - 1:
                print(f"Retrying in {retry_delay} seconds...")
                await asyncio.sleep(retry_delay)
            else:
                print("Failed to initialize vector stores after all retries")
                print("Run 'python scripts/setup_database.py' to set up the database")
                return False

def startup_handler():
    """Handle application startup tasks with better error handling."""
    try:
        # Initialize vector stores in background
        asyncio.create_task(initialize_vector_stores())
        print("✓ Startup tasks initiated")
    except Exception as e:
        print(f"Startup handler error: {e}")