# app/tools/__init__.py
"""
Tools package for HeyLisa.

Each tool exposes a `run()` method and is orchestrated by the OrchestratorAgent.
"""

from app.tools.web_search import WebSearchTool

__all__ = [
    "WebSearchTool",
]