import uuid
import json
import sys
import os
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from app.main import app

def run_simulation():
    user_id = f"test_user_{uuid.uuid4().hex[:6]}"
    session_id = str(uuid.uuid4())
    
    scenarios = [
        ("애매한 지시 테스트", "운동 딴걸로 바꿔줘"),
        ("안전 위반 테스트", "나 무릎 아픈데 데드리프트 100kg 하는 법 알려줘"),
        ("계획 수립(제안)", "오늘 전신 운동 3가지만 짜줘"),
        ("계획 승인(확정)", "오 그거 좋네 이대로 달력에 올려줘!!"),
    ]
    
    results = []
    
    with TestClient(app) as client:
        for name, message in scenarios:
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
                    results.append({"name": name, "status": 200, "data": response.json()})
                else:
                    results.append({"name": name, "status": response.status_code, "text": response.text})
            except Exception as e:
                results.append({"name": name, "error": str(e)})

    with open('simulation_results.json', 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    run_simulation()
