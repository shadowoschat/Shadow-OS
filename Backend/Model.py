import logging

try:
    import cohere
except ImportError:  # pragma: no cover
    cohere = None

from Backend.config import get_env
from Backend.Database.memory_db import get_user_memory, save_short_term_memory

logger = logging.getLogger(__name__)

funcs = [
    "exit", "general", "realtime", "open", "close", "play",
    "generate image", "system", "content", "google search",
    "youtube search", "project_creator"
]

CohereAPIKey = get_env("COHERE_API_KEY")
co = cohere.Client(api_key=CohereAPIKey) if cohere and CohereAPIKey else None

preamble = """
You are a highly accurate Decision-Making Model, which decides what kind of a query is given to you.
You will reply with only a single word from the provided list, or if the user asks a question, provide a detailed response followed by (query).
[List of functions]
"""


def _safe_classify_response(raw_response):
    if raw_response is None:
        return []
    if isinstance(raw_response, list):
        items = raw_response
    else:
        items = str(raw_response).replace("\n", "").split(",")

    normalized = []
    for item in items:
        if not isinstance(item, str):
            item = str(item)
        cleaned = item.strip()
        if not cleaned:
            continue
        normalized.append(cleaned)

    selected = []
    for task in normalized:
        for func in funcs:
            if task.lower().startswith(func.lower()):
                selected.append(task)
    return selected


def FirstLayerDMM(prompt: str = "test", user_id: str = None):
    if not prompt or not str(prompt).strip():
        return ["general"]

    if not co:
        return ["general"]

    try:
        stream = co.chat(
            model="command-r-plus-08-2024",
            message=prompt,
            temperature=0.7,
            prompt_truncation='OFF',
            connectors=[],
            preamble=preamble,
        )

        response = ""
        for event in stream:
            if isinstance(event, tuple) and len(event) > 1 and event[0] == 'text':
                response = str(event[1])
            if hasattr(event, 'event_type') and getattr(event, 'event_type', None) == "text-generation":
                response += str(getattr(event, 'text', ''))

        tasks = _safe_classify_response(response)
        if not tasks:
            return ["general"]
        return tasks
    except Exception as exc:
        logger.warning("Cohere DMM failed; falling back to direct general chat: %s", exc)
        return ["general"]


class ShadowMemoryManager:
    """Manages memory per user context using PostgreSQL"""
    def __init__(self, user_id: str):
        self.user_id = user_id
        if user_id:
            self.memory = get_user_memory(user_id)
        else:
            self.memory = {"user_name": "User", "short_term_memory": [], "interactions": []}

    def update_context_for_llm(self, system_prompt):
        user_name = self.memory.get("user_name", "User")
        recent_memories = self.memory.get("short_term_memory", [])[-5:]
        context = f"You are chatting with {user_name}.\nRecent context:\n"
        for mem in recent_memories:
            context += f"User: {mem.get('query', '')}\nAI: {mem.get('response', '')}\n"
        return system_prompt + "\n" + context

    def add_short_term_context(self, query, response):
        if self.user_id:
            save_short_term_memory(self.user_id, {"query": query, "response": response})
