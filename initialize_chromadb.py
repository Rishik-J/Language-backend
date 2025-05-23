import os
import logging
import time
import chromadb
from chromadb import Settings

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

def initialize_chromadb():
    """Initialize ChromaDB with collections and initial data if needed."""
    
    # Wait for ChromaDB to be ready (in case this runs during container startup)
    retries = 5
    retry_delay = 5  # seconds
    
    for attempt in range(retries):
        try:
            # Set up client
            host = os.getenv("CHROMA_HOST", "localhost")
            port = int(os.getenv("CHROMA_PORT", "8000"))
            
            logging.info(f"Connecting to ChromaDB at {host}:{port} (attempt {attempt+1}/{retries})")
            
            client = chromadb.HttpClient(
                host=host,
                port=port,
                settings=Settings(
                    chroma_client_auth_provider="token",
                    chroma_client_auth_credentials=os.getenv("CHROMA_TOKEN", "")
                )
            )
            
            # Test connection
            client.heartbeat()
            logging.info("Successfully connected to ChromaDB")
            
            # Create architect-docs collection if it doesn't exist
            collection_name = os.getenv("CHROMA_COLLECTION", "architect-docs")
            collections = client.list_collections()
            collection_exists = any(col.name == collection_name for col in collections)
            
            if not collection_exists:
                logging.info(f"Creating collection: {collection_name}")
                client.create_collection(
                    name=collection_name,
                    metadata={"hnsw:space": "cosine"}
                )
                logging.info(f"Successfully created collection: {collection_name}")
            else:
                logging.info(f"Collection {collection_name} already exists")
            
            # Add seed data if needed
            # This would typically call your existing seeding scripts
            # Example: import Scripts.seed_component_docs
            #          Scripts.seed_component_docs.run()
            
            logging.info("ChromaDB initialization complete")
            break
            
        except Exception as e:
            logging.warning(f"ChromaDB connection attempt {attempt+1}/{retries} failed: {e}")
            if attempt < retries - 1:
                logging.info(f"Retrying in {retry_delay} seconds...")
                time.sleep(retry_delay)
            else:
                logging.error(f"Failed to initialize ChromaDB after {retries} attempts")
                raise

if __name__ == "__main__":
    initialize_chromadb() 