import asyncio
from app.llm.runtime import LLMRuntime

async def main():
    llm = LLMRuntime()
    text, meta = await llm.chat_text(
        [{"role":"user","content":"Réponds juste: OK"}],
        temperature=0.0,
        max_tokens=20,
    )
    print("TEXT:", text)
    print("META:", meta)

asyncio.run(main())