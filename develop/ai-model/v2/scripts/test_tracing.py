import httpx
import json
import sys


def test_chat():
    if sys.platform == "win32":
        sys.stdout.reconfigure(encoding="utf-8")

    url = "http://127.0.0.1:8000/chat"
    payload = {
        "user_id": "tester_123",
        "user_message": "안녕? 나 오늘 하체 운동하고 싶은데 ESTJ스럽게 논리적인 근거랑 같이 짜줘.",
        "user_profile_override": {
            "selected_ai_persona": "default",
            "mbti": "ESTJ",
            "goal": "근력 증진",
        },
    }

    try:
        with httpx.Client(timeout=60.0) as client:
            response = client.post(url, json=payload)
            print(f"Status Code: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                print("\n[Final Response]")
                print(data["response"])
                print("\n[Draft Response (Should be dry)]")
                print(data.get("draft_response"))
                print("\n[Debug State]")
                print(json.dumps(data.get("debug_state"), indent=2, ensure_ascii=False))
            else:
                print(f"Error: {response.text}")
    except Exception as e:
        print(f"Exception: {e}")


if __name__ == "__main__":
    test_chat()
