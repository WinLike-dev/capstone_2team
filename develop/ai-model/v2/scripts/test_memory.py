import asyncio
from app.core._container import init_container
from app.graph.nodes.feedback import execute_feedback

async def main():
    deps = init_container()
    
    # 1. 초기 팩트 강제 입력
    print("--- 1. 초기 팩트 세팅 ---")
    user_id = "test_user_memory"
    # 기존 팩트는 모두 지우기
    empty_vec = await getattr(deps, 'embed').embed("empty")
    res = await getattr(deps, 'pinecone').search_important(user_id, empty_vec, top_k=10)
    if res:
        await getattr(deps, 'pinecone').delete_important(user_id, [r['id'] for r in res])
        
    vec1 = await getattr(deps, 'embed').embed("현재 체중은 80kg이다.")
    await getattr(deps, 'pinecone').upsert_important(user_id, vec1, "현재 체중은 80kg이다.")
    print("초기 팩트 세팅 완료: 현재 체중은 80kg이다.")
    
    print("\n--- 2. Active Memory Manager 실행 (ADD/UPDATE 실험) ---")
    message = "나 다이어트 엄청 열심히 해서 드디어 75kg 찍었어!! 그리고 나 우유 알레르기도 생겼어 ㅠㅠ"
    response = "우와, 정말 대단하세요! 75kg 달성을 축하드립니다. 우유 알레르기가 생기셨다니 식단을 조심해야겠네요."
    
    await execute_feedback(
        deps=deps,
        user_id=user_id,
        user_message=message,
        response=response,
        should_save_episode=False,
        emotion_label="기쁨",
        emotion_intensity=0.9
    )
    
    print("\n--- 3. 결과 확인 ---")
    res2 = await getattr(deps, 'pinecone').search_important(user_id, empty_vec, top_k=10)
    for r in res2:
        print(f"저장된 팩트: {r['text']} (점수: {r['score']})")

if __name__ == "__main__":
    asyncio.run(main())
