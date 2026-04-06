import os
import json
import asyncio
import logging
from dotenv import load_dotenv
from pinecone import Pinecone

# Ensure we can import from app
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.clients.embedding import EmbeddingClient
from app.clients.pinecone import PineconeClient
from pinecone import PineconeAsyncio

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

load_dotenv()

async def ingest():
    # 1. API Keys and Clients
    gemini_key = os.getenv("GEMINI_API_KEY") or os.getenv("ROUTER_API_KEY")
    pinecone_key = os.getenv("PINECONE_API_KEY")
    index_name = os.getenv("PINECONE_INDEX_NAME", "health-coach-ai")

    if not gemini_key or not pinecone_key:
        logger.error("API keys (GEMINI/PINECONE) not found in .env")
        return

    embed_client = EmbeddingClient(api_key=gemini_key)
    pc_core = PineconeAsyncio(api_key=pinecone_key)
    
    # Get index host
    description = await pc_core.describe_index(index_name)
    index = pc_core.IndexAsyncio(host=description.host)
    pc_client = PineconeClient(index=index)

    # 2. Load Data
    data_path = os.path.join(os.path.dirname(__file__), '../data/external_knowledge.json')
    try:
        with open(data_path, 'r', encoding='utf-8') as f:
            knowledge_items = json.load(f)
    except Exception as e:
        logger.error(f"Failed to load JSON data: {e}")
        return

    logger.info(f"Starting ingestion of {len(knowledge_items)} items...")

    # 3. Processing
    success_count = 0
    for i, item in enumerate(knowledge_items):
        try:
            text = item['text']
            source = item['source']
            category = item['category']
            tags = item.get('tags', [])
            extra_metadata = {
                key: value
                for key, value in item.items()
                if key not in {"text", "source", "category", "tags"}
            }

            logger.info(f"[{i+1}/{len(knowledge_items)}] Embedding: {source} ({category})...")
            
            # Use EmbeddingClient
            vector = await embed_client.embed(text)
            
            # Use PineconeClient expansion
            await pc_client.upsert_external(
                vector=vector,
                text=text,
                source=source,
                category=category,
                tags=tags,
                extra_metadata=extra_metadata,
            )
            success_count += 1
            logger.info(f"Successfully upserted: {source}")
            
            # Small sleep to avoid rate limiting if needed
            await asyncio.sleep(0.5)
            
        except Exception as e:
            logger.error(f"Error at item {i+1}: {e}")

    logger.info(f"Ingestion complete! Success: {success_count}/{len(knowledge_items)}")

if __name__ == "__main__":
    asyncio.run(ingest())
