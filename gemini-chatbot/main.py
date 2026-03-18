from fastapi import FastAPI
from pydantic import BaseModel
from langchain_google_genai import ChatGoogleGenerativeAI
from dotenv import load_dotenv
import os

# 1. .env 파일에 있는 환경 변수(API 키)를 불러옵니다.
load_dotenv()

# 2. FastAPI 앱 초기화
app = FastAPI(title="Gemini Chatbot API")

# 3. LangChain을 통해 제미니 Flash 모델 연결
# GOOGLE_API_KEY는 환경 변수에서 자동으로 읽어옵니다.
llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash")

# 4. 사용자가 보낼 데이터 구조(스키마) 정의
class ChatRequest(BaseModel):
    user_input: str

# 5. POST 방식의 /chat 엔드포인트 생성
@app.post("/chat")
async def chat_endpoint(request: ChatRequest):
    # LangChain의 invoke 메서드로 제미니에게 질문 전달
    response = llm.invoke(request.user_input)
    
    # 챗봇의 답변을 JSON 형태로 반환
    return {
        "question": request.user_input,
        "answer": response.content
    }