import datetime
import logging
import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from Backend.config import get_env
from Backend.Database.chat_db import get_chat_history, save_chat_message
from Backend.Model import ShadowMemoryManager

logger = logging.getLogger(__name__)

Username = get_env("USERNAME", "User")
Assistantname = get_env("ASSISTANT_NAME", "Shadow")

try:
    from groq import Groq
except ImportError:  # pragma: no cover
    Groq = None


def _get_groq_client():
    api_key = get_env("GROQ_API_KEY")
    if not api_key:
        raise RuntimeError("GROQ_API_KEY is missing")
    if Groq is None:
        raise RuntimeError("groq package is not installed")
    return Groq(api_key=api_key)


System = f"""You are {Assistantname}, a smart, respectful, premium, and highly user-friendly personal AI assistant for {Username}.

## Core Behavior Rules:
- Respond in a natural, polished, human-like way — never robotic, repetitive, or bland.
- Always make conversations feel warm, intelligent, and personalized.
- Use {Username} naturally when appropriate. Do not overuse.
- Use {Assistantname} when introducing yourself or adding polish.
- Keep responses concise, helpful, and natural.
"""


def RealtimeInformation():
    current_date_time = datetime.datetime.now()
    day = current_date_time.strftime("%A")
    date = current_date_time.strftime("%d")
    month = current_date_time.strftime("%B")
    year = current_date_time.strftime("%Y")
    hour = current_date_time.strftime("%H")
    minute = current_date_time.strftime("%M")
    second = current_date_time.strftime("%S")

    data = f"Please use this real-time information if needed:\n"
    data += f"Day: {day}\nDate: {date}\nMonth: {month}\nYear: {year}\n"
    data += f"Time: {hour} hours, {minute} minutes, {second} seconds.\n"
    return data


def AnswerModifier(Answer):
    lines = Answer.split('\n')
    non_empty_lines = [line for line in lines if line.strip()]
    return '\n'.join(non_empty_lines)


def ChatBot(Query, user_id=None, save_history=False):
    """Send query to chatbot and return response, with memory management."""
    if Query is None:
        raise ValueError("Chat message is required")

    query_text = str(Query).strip()
    if not query_text:
        raise ValueError("Chat message is required")

    client = _get_groq_client()
    try:
        messages = []
        if user_id:
            messages = get_chat_history(user_id, limit=20)

        messages.append({"role": "user", "content": query_text})

        memory = ShadowMemoryManager(user_id)
        enhanced_system = memory.update_context_for_llm(System)
        model_name = get_env("GROQ_CHAT_MODEL", "openai/gpt-oss-120b")

        completion = client.chat.completions.create(
            model=model_name,
            messages=[
                {"role": "system", "content": enhanced_system},
                {"role": "system", "content": RealtimeInformation()},
            ] + messages[-10:],
            max_tokens=520,
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

        answer = answer.replace("</s>", "").strip()
        if not answer:
            answer = "I'm having trouble formulating a response. Could you rephrase that?"

        if user_id and save_history:
            save_chat_message(user_id, "user", query_text)
            save_chat_message(user_id, "assistant", answer)
            memory.add_short_term_context(query_text, answer)

        return answer

    except Exception as exc:
        logger.exception("Groq ChatBot request failed")
        raise RuntimeError(f"Groq provider error: {exc}") from exc
