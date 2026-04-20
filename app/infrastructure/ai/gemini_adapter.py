from typing import List
from google import genai
from ...domain.entities import Message
from ...domain.providers.base import AiProvider

class GeminiAdapter(AiProvider):
    def __init__(self, api_key: str, system_prompt: str):
        self.client = genai.Client(api_key=api_key)
        self.system_prompt = system_prompt

    async def send_message(self, message: str, history: List[Message], model_id: str) -> str:
        # Adaptar historial a formato Gemini
        gemini_history = []
        for m in history:
            role = "user" if m.role == "user" else "model"
            gemini_history.append({"role": role, "parts": [{"text": m.content}]})
        
        session = self.client.chats.create(
            model=model_id,
            history=gemini_history,
            config={"system_instruction": self.system_prompt}
        )
        response = session.send_message(message)
        return response.text
