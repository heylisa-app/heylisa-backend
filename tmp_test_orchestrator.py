import asyncio
from app.llm.runtime import LLMRuntime
from app.agents.orchestrator import OrchestratorAgent

async def main():
    llm = LLMRuntime()
    agent = OrchestratorAgent(llm)

    for msg in [
        "Bonne nuit Lisa",
        "Peux-tu me rappeler ce que tu peux faire ?",
        "Je panique, j'ai un truc urgent là",
        "Aide-moi à décider entre deux options pro",
    ]:
        r = await agent.run(user_message=msg)
        print("\nUSER:", msg)
        print("OK:", r.ok, "intent:", r.intent, "level:", r.context_level, "conf:", r.confidence)
        print("PLAN:", r.plan)

asyncio.run(main())