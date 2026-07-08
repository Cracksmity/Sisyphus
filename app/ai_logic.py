import os
import traceback
from openai import AsyncOpenAI

def get_client():
    # Fetch API key to instantiate client (handles runtime loading perfectly)
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        print("WARNING: OPENAI_API_KEY is not set.")
    return AsyncOpenAI(api_key=api_key)

async def generate_chat_response(messages: list, system_prompt: str, model="gpt-4o", max_tokens: int = 1500):
    client = get_client()
    try:
        formatted_messages = [{"role": "system", "content": system_prompt}]
        for msg in messages:
            formatted_messages.append({"role": msg["role"], "content": msg["content"]})
        
        response = await client.chat.completions.create(
            model=model,
            messages=formatted_messages,
            temperature=0.7,
            max_tokens=max_tokens
        )
        return response.choices[0].message.content
    except Exception:
        print(f"Error in OpenAI call:\n{traceback.format_exc()}")
        raise
