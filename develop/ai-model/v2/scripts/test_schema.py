import asyncio
from google import genai
from google.genai import types
from pydantic import BaseModel, Field
from typing import Optional, Literal
import os

api_key = "AIzaSyAWJ1iFUh57ORhrGYHsH0abDF7h4_w-D7E"
client = genai.Client(api_key=api_key)

class ProfileChange(BaseModel):
    field: str
    value: str

class TestSchema(BaseModel):
    intent: str
    # profile_changes: Optional[dict] = None  # This triggers the error
    profile_changes: Optional[list[ProfileChange]] = None

async def test():
    try:
        response = await client.aio.models.generate_content(
            model="gemini-2.5-flash",
            contents="hello",
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=TestSchema,
            )
        )
        print("Success:", response.text)
    except Exception as e:
        print("Error:", e)

if __name__ == "__main__":
    asyncio.run(test())
