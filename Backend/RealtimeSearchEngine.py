import datetime
import logging
from pathlib import Path

from Backend.config import get_env

logger = logging.getLogger(__name__)

try:
    from googlesearch import search
except ImportError:  # pragma: no cover
    search = None

try:
    from groq import Groq
except ImportError:  # pragma: no cover
    Groq = None


ROOT_DIR = Path(__file__).resolve().parent.parent
Username = get_env("USERNAME", "User")
Assistantname = get_env("ASSISTANT_NAME", "Shadow")


def _get_groq_client():
    api_key = get_env("GROQ_API_KEY")
    if not api_key:
        raise RuntimeError("GROQ_API_KEY is missing")
    if Groq is None:
        raise RuntimeError("groq package is not installed")
    return Groq(api_key=api_key)


System = f"""Hello, I am {Username}. You are a very accurate and advanced AI chatbot named {Assistantname}.
*** Provide answers in a professional way with proper grammar. ***
*** If no search results are found, say so clearly. ***"""


def GoogleSearch(query):
    if search is None:
        return f"Search provider is unavailable for '{query}'."
    try:
        results = list(search(query, advanced=True, num=5))
        if not results:
            return f"No search results found for '{query}'."
        answer = f"The search results for '{query}' are:\n[start]\n"
        for item in results:
            title = getattr(item, 'title', str(item))
            description = getattr(item, 'description', '')
            answer += f"Title: {title}\nDescription: {description}\n\n"
        answer += "[end]"
        return answer
    except Exception as exc:
        logger.warning("Google search failed: %s", exc)
        return f"Search failed for '{query}'."


def AnswerModifier(Answer):
    lines = Answer.split('\n')
    non_empty_lines = [line for line in lines if line.strip()]
    return '\n'.join(non_empty_lines)


def Information():
    date = datetime.datetime.now()
    return (
        f"Use this real-time information if needed:\n"
        f"Day: {date.strftime('%A')}\n"
        f"Date: {date.strftime('%d')}\n"
        f"Month: {date.strftime('%B')}\n"
        f"Year: {date.strftime('%Y')}\n"
        f"Time: {date.strftime('%H')} hours: {date.strftime('%M')} minutes: {date.strftime('%S')} seconds.\n"
    )


def RealtimeSearchEngine(prompt, user_id=None):
    question = str(prompt or '').strip()
    if not question:
        raise ValueError("Prompt is required")

    search_data = GoogleSearch(question)
    messages = [
        {"role": "system", "content": System},
        {"role": "user", "content": question},
    ]

    try:
        client = _get_groq_client()
        model_name = get_env("GROQ_REALTIME_MODEL", "meta-llama/llama-4-scout-17b-16e-instruct")
        completion = client.chat.completions.create(
            model=model_name,
            messages=messages + [{"role": "system", "content": Information()}],
            max_tokens=1024,
            temperature=0.7,
            top_p=1,
            stream=True,
            stop=None,
        )
        answer = ""
        for chunk in completion:
            try:
                content = chunk.choices[0].delta.content
                if content:
                    answer += content
            except (AttributeError, IndexError):
                continue
        answer = answer.strip().replace("</s>", "")
        return search_data + "\nFinal summarized answer based only on the search data.\n" + AnswerModifier(answer)
    except Exception as exc:
        logger.warning("Realtime search fallback response used: %s", exc)
        return search_data + "\nFinal summarized answer based only on the search data.\n" + "I could not complete the live AI summary, but the search results are above."
