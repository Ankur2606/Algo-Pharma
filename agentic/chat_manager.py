"""
AlgoPharma — Slot-filling chat manager.

Uses Nvidia Nemotron (via the OpenAI-compatible SDK) to maintain a JSON
state dict across chat turns and ask follow-up questions until all
mandatory fields (medicine, source) are gathered.

State schema:
  {
    "medicine": str | null,   # MANDATORY
    "source":   str | null,   # MANDATORY — one of: reddit, twitter, custom_forum
    "symptom":  str | null,   # OPTIONAL — bot asks once, accepts skip
  }

Returns when mandatory fields are filled:
  bot_message == "READY"

Usage:
  new_state, bot_message = get_nemotron_response(user_message, current_state)
"""

import json
import logging
import os
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

# ── Sentinel returned when all mandatory fields are populated ──────────
READY_SIGNAL = "READY"

SYSTEM_PROMPT = """\
You are a pharmacovigilance data-gathering assistant for AlgoPharma.
Your job is to collect exactly three fields from the user through friendly conversation:

FIELDS:
- medicine  (MANDATORY): the drug or medicine name the user wants to investigate
- source    (MANDATORY): where to search — MUST be exactly one of: reddit, twitter, custom_forum
- symptom   (OPTIONAL):  a specific adverse symptom or side effect to focus on

RULES:
1. Each turn you receive the current state (as JSON) and the user's latest message.
2. Extract any new information from the message and update the state.
3. If "source" is mentioned as "forum" or "custom forum" or "1mg" or similar, normalise it to "custom_forum".
4. Ask for symptom EXACTLY ONCE — after medicine and source are confirmed. If the user skips,
   says "no", "skip", "any", or gives a vague reply, set symptom to null and proceed.
5. The moment BOTH "medicine" and "source" are non-null (symptom may still be null),
   set bot_message to the EXACT string "READY" — nothing else.
6. Keep replies conversational and concise. Use simple English.

RESPONSE FORMAT — return ONLY valid JSON, no markdown fences, no extra text:
{
  "state": {
    "medicine": "<string or null>",
    "source": "<reddit|twitter|custom_forum|null>",
    "symptom": "<string or null>"
  },
  "bot_message": "<your conversational reply, OR the exact string READY>"
}
"""


import re

def _fallback_question(state: dict) -> str:
    """Generate a sensible question based on what's still missing — no LLM needed."""
    if not state.get("medicine"):
        return "Could you tell me the name of the medicine you'd like to investigate?"
    if not state.get("source"):
        return f"Got it — {state['medicine']}! Where should I search? Please choose: **Reddit**, **Twitter**, or a **Custom Forum**."
    # Both mandatory fields present
    return READY_SIGNAL


def _extract_json(text: str) -> dict | None:
    """Try to extract a JSON object from raw text (handles markdown fences, thinking preamble)."""
    # Strip leading thinking/reasoning preamble that Nemotron sometimes emits
    # Look for the first { ... } block
    text = text.strip()
    # Remove markdown fences
    text = re.sub(r"^```(?:json)?\s*", "", text)
    text = re.sub(r"\s*```$", "", text)
    text = text.strip()

    # Find outermost JSON object
    start = text.find("{")
    if start == -1:
        return None
    depth = 0
    for i, ch in enumerate(text[start:], start):
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                try:
                    return json.loads(text[start : i + 1])
                except json.JSONDecodeError:
                    return None
    return None


def get_nemotron_response(message: str, state: dict) -> tuple[dict, str]:
    """
    Call Groq (llama-3.3-70b-versatile) to update the slot-filling state.

    Groq is much faster than Nemotron for this task — no extended thinking overhead.
    Uses streaming for lowest latency as per Groq's recommended pattern.

    Returns:
        (new_state, bot_message) — if bot_message == "READY" trigger the pipeline.
    """
    from config import get_settings
    settings = get_settings()

    api_key = settings.GROQ_API_KEY
    if not api_key:
        logger.warning("[chat_manager] GROQ_API_KEY not set — using fallback questions")
        new_state = dict(state)
        msg_lower = message.lower()
        if not new_state.get("medicine"):
            words = [w for w in message.split() if len(w) > 2]
            if words:
                new_state["medicine"] = words[0].title()
        elif not new_state.get("source"):
            for src in ["reddit", "twitter"]:
                if src in msg_lower:
                    new_state["source"] = src
                    break
            if "forum" in msg_lower or "1mg" in msg_lower or "custom" in msg_lower:
                new_state["source"] = "custom_forum"
        return new_state, _fallback_question(new_state)

    try:
        from groq import Groq
        client = Groq(api_key=api_key)

        state_str = json.dumps(state, indent=2)
        user_turn = (
            f"Current state:\n{state_str}\n\n"
            f"User message: {message}"
        )

        logger.debug(f"[chat_manager] Calling Groq | state={state} | msg={message!r}")

        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user",   "content": user_turn},
            ],
            temperature=0.3,
            max_completion_tokens=512,
            top_p=1,
            stream=True,
            stop=None,
        )

        # Collect streamed chunks
        raw = ""
        for chunk in completion:
            raw += chunk.choices[0].delta.content or ""

        raw = raw.strip()
        logger.debug(f"[chat_manager] Groq response: {raw!r}")

        # Parse JSON — model may wrap in markdown fences
        data = _extract_json(raw)
        if data is None:
            logger.warning(f"[chat_manager] No JSON in Groq response, using fallback | raw={raw[:200]!r}")
            return state, _fallback_question(state)

        new_state   = data.get("state", state)
        bot_message = data.get("bot_message", "") or ""

        # Sanitise — preserve previously filled fields if model drops them
        new_state.setdefault("medicine", state.get("medicine"))
        new_state.setdefault("source",   state.get("source"))
        new_state.setdefault("symptom",  state.get("symptom"))

        # If bot_message empty, generate deterministic fallback
        if not bot_message.strip():
            bot_message = _fallback_question(new_state)

        # Hard guard: mandatory fields filled → always READY
        if new_state.get("medicine") and new_state.get("source"):
            bot_message = READY_SIGNAL

        return new_state, bot_message

    except Exception as e:
        logger.error(f"[chat_manager] Groq call failed: {e}")
        return state, _fallback_question(state)


