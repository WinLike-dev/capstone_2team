"""Pinecone 인덱스 초기화 및 네임스페이스 확인 스크립트."""
import os
import sys
from dotenv import load_dotenv

load_dotenv()

from pinecone import Pinecone, ServerlessSpec

PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
INDEX_NAME = os.getenv("PINECONE_INDEX_NAME", "health-coach-ai")
EMBEDDING_DIM = 384

def main():
    print(f"=== Pinecone 초기화 ===")
    print(f"Index Name : {INDEX_NAME}")
    print(f"Dimension  : {EMBEDDING_DIM}")
    print()

    pc = Pinecone(api_key=PINECONE_API_KEY)

    # 1. 기존 인덱스 목록 확인
    existing = [idx.name for idx in pc.list_indexes()]
    print(f"기존 인덱스 목록: {existing}")

    # 2. 인덱스 생성 (없으면)
    if INDEX_NAME not in existing:
        print(f"\n'{INDEX_NAME}' 인덱스 생성 중...")
        pc.create_index(
            name=INDEX_NAME,
            dimension=EMBEDDING_DIM,
            metric="cosine",
            spec=ServerlessSpec(cloud="aws", region="us-east-1"),
        )
        print("✅ 인덱스 생성 완료!")
    else:
        print(f"\n✅ '{INDEX_NAME}' 인덱스가 이미 존재합니다.")

    # 3. 인덱스 상세 정보
    desc = pc.describe_index(INDEX_NAME)
    print(f"\n=== 인덱스 상세 ===")
    print(f"Host       : {desc.host}")
    print(f"Dimension  : {desc.dimension}")
    print(f"Metric     : {desc.metric}")
    print(f"Status     : {desc.status}")

    # 4. 인덱스 통계
    index = pc.Index(INDEX_NAME)
    stats = index.describe_index_stats()
    print(f"\n=== 인덱스 통계 ===")
    print(f"Total vectors: {stats.total_vector_count}")
    if stats.namespaces:
        for ns, ns_stats in stats.namespaces.items():
            print(f"  namespace '{ns}': {ns_stats.vector_count} vectors")
    else:
        print("  (아직 네임스페이스 없음 — 첫 upsert 시 자동 생성됨)")

    # 5. 네임스페이스 설계 요약
    print(f"\n=== 네임스페이스 설계 ===")
    print(f"  vdb_memory          : {{user_id}}-memory     (에피소드·추억, per user)")
    print(f"  vdb_user_important  : {{user_id}}-important  (핵심 팩트 요약, per user)")
    print(f"  vdb_external        : external              (외부 운동·영양 지식, 공유)")
    print(f"\n✅ Pinecone 준비 완료!")

if __name__ == "__main__":
    main()
