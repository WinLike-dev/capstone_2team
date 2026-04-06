"""능동형 메모리 매니저(Active Memory Manager) 포함 시뮬레이션.

시나리오:
1. 첫 턴: "나 다이어트 시작했어 현재 몸무게 80kg이야" → ADD 예상
2. 두 번째: "오늘 웨이트 트레이닝 계획 짜줘" → 일반 질문 (KEEP, no changes)
3. 세 번째: "와 드디어 75kg 달성했어!" → UPDATE 예상 (80kg → 75kg)
4. 네 번째: "그리고 나 우유 알레르기 생겼어 ㅠ" → ADD 예상 (새 팩트)

서버 로그에서 ActiveMemoryManager 관련 로그를 확인하세요.
"""
import uuid
import json
import sys
import os
import logging
import asyncio
from fastapi.testclient import TestClient

# 로그 레벨 세팅 -  ActiveMemoryManager 로그 확인용
logging.basicConfig(level=logging.INFO)

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from app.main import app


def run_simulation():
    user_id = f"test_mem_{uuid.uuid4().hex[:6]}"
    session_id = str(uuid.uuid4())

    scenarios = [
        ("팩트_등록", "나 다이어트 시작했어. 현재 몸무게 80kg이야."),
        ("일반_질문", "오늘 웨이트 트레이닝 계획 짜줘"),
        ("팩트_업데이트", "와 드디어 75kg 달성했어! 체중 업데이트 해줘"),
        ("팩트_추가", "그리고 나 우유 알레르기 생겼어 ㅠㅠ"),
    ]

    results = []

    with TestClient(app) as client:
        for name, message in scenarios:
            print(f"\n{'='*60}")
            print(f"[시나리오: {name}] 메시지: {message}")
            print(f"{'='*60}")
            try:
                response = client.post(
                    "/chat",
                    json={
                        "user_id": user_id,
                        "session_id": session_id,
                        "user_message": message
                    }
                )
                if response.status_code == 200:
                    data = response.json()
                    results.append({"name": name, "status": 200, "data": data})
                    print(f"  → 의도: {data.get('intent')}")
                    print(f"  → 감정: {data.get('emotion')}")
                    print(f"  → 응답(일부): {data.get('response', '')[:100]}...")
                else:
                    results.append({"name": name, "status": response.status_code, "text": response.text})
                    print(f"  → 오류: {response.status_code} {response.text[:200]}")
            except Exception as e:
                results.append({"name": name, "error": str(e)})
                print(f"  → 예외: {e}")

    with open('simulation_memory_results.json', 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    print(f"\n{'='*60}")
    print(f"시뮬레이션 완료. 결과: simulation_memory_results.json")
    print(f"서버 로그에서 'ActiveMemoryManager' 를 검색하세요.")
    print(f"{'='*60}")


if __name__ == "__main__":
    run_simulation()
