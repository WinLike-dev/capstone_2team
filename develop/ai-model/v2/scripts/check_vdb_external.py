import os
import asyncio
from dotenv import load_dotenv
from pinecone import Pinecone

load_dotenv()

async def check():
    api_key = os.getenv("PINECONE_API_KEY")
    index_name = os.getenv("PINECONE_INDEX_NAME", "health-coach-ai")
    
    pc = Pinecone(api_key=api_key)
    index = pc.Index(index_name)
    
    # query the 'external' namespace with a dummy vector or just describe stats
    print(f"Index: {index_name}")
    stats = index.describe_index_stats()
    print(f"Stats: {stats}")
    
    if "external" in stats.namespaces:
        # Try to fetch some vectors from 'external' namespace
        # Since I don't have the vectors, I'll use a dummy query vector (assuming dim=384)
        dummy_vector = [0.0] * 384
        res = index.query(
            vector=dummy_vector,
            top_k=5,
            namespace="external",
            include_metadata=True
        )
        print("\n=== External VDB Content (Top 5 Samples) ===")
        for match in res.matches:
            print(f"- ID: {match.id}")
            print(f"  Score: {match.score}")
            print(f"  Metadata: {match.metadata}")
            print("---")
    else:
        print("\n'external' namespace not found.")

if __name__ == "__main__":
    asyncio.run(check())
