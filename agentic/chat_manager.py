"""
AlgoPharma — Slot-filling chat manager.

Uses Nvidia Nemotron (via the OpenAI-compatible SDK) to maintain a JSON
state dict across chat turns and ask follow-up questions until all
mandatory fields (medicine, source) are gathered.

State schema:
  {
    "medicine":  str | null,   # MANDATORY
    "source":    str | null,   # MANDATORY — one of: reddit, twitter, custom_forum
    "symptom":   str | null,   # OPTIONAL — bot asks once, accepts skip
    "forum_url": str | null,   # CONDITIONAL — MANDATORY when source == custom_forum
  }

Returns when mandatory fields are filled:
  bot_message == "READY"

Usage:
  new_state, bot_message = get_nemotron_response(user_message, current_state)
"""

import json
import logging
import os
import re
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

# ── Sentinel returned when all mandatory fields are populated ──────────
READY_SIGNAL = "READY"

SYSTEM_PROMPT = """\
You are a pharmacovigilance data-gathering assistant for AlgoPharma.
Your job is to collect these fields from the user through friendly conversation:

FIELDS:
- medicine   (MANDATORY): the drug or medicine name the user wants to investigate
- source     (MANDATORY): where to search — MUST be exactly one of: reddit, twitter, custom_forum
- symptom    (OPTIONAL):  a specific adverse symptom or side effect to focus on
- forum_url  (CONDITIONAL): if source is "custom_forum", extract the full URL from the message.
                           Look for any http:// or https:// link. If no link is found, set to null.

RULES:
1. Each turn you receive the current state (as JSON) and the user's latest message.
2. Extract any new information from the message and update the state.
3. If the user message does not contain a medicine or source, DO NOT guess or make them up. Leave them as null.
4. If "source" is mentioned as "forum" or "custom forum" or "1mg" or similar, normalise it to "custom_forum".
5. If the user provides a URL (http:// or https://), ALWAYS capture it in forum_url and set source to "custom_forum".
6. Ask for symptom EXACTLY ONCE — after medicine and source are confirmed. If the user skips,
   says "no", "skip", "any", or gives a vague reply, set symptom to null and proceed.
7. If source is "custom_forum" and forum_url is null, ask for the forum URL before returning READY.
8. The moment BOTH "medicine" and "source" are non-null (and forum_url is set if source is custom_forum),
   set bot_message to the EXACT string "READY" — nothing else.
9. Keep replies conversational and concise. Use simple English.

RESPONSE FORMAT — return ONLY valid JSON, no markdown fences, no extra text:
{
  "state": {
    "medicine": "<string or null>",
    "source": "<reddit|twitter|custom_forum|null>",
    "symptom": "<string or null>",
    "forum_url": "<full URL or null>"
  },
  "bot_message": "<your conversational reply, OR the exact string READY>"
}
"""


def _extract_url(text: str) -> str | None:
    """Pull the first http(s) URL out of a message."""
    m = re.search(r'https?://[^\s,)]+', text)
    return m.group(0).rstrip('.,;') if m else None


def _fallback_question(state: dict) -> str:
    """Generate a sensible question based on what's still missing — no LLM needed."""
    if not state.get("medicine"):
        return "Could you tell me the name of the medicine you'd like to investigate?"
    if not state.get("source"):
        return f"Got it — {state['medicine']}! Where should I search? Please choose: **Reddit**, **Twitter**, or a **Custom Forum**."
    # If custom_forum, we need a URL
    if state.get("source") == "custom_forum" and not state.get("forum_url"):
        return f"Great — I'll search a custom forum for {state['medicine']}. Could you share the forum URL?"
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
        # Always try to capture a URL from the message
        url_in_msg = _extract_url(message)
        if url_in_msg:
            new_state["forum_url"] = url_in_msg
            new_state.setdefault("source", "custom_forum")
        if not new_state.get("medicine"):
            words = [w for w in message.split() if len(w) > 2 and not w.startswith('http')]
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
        new_state.setdefault("medicine",  state.get("medicine"))
        new_state.setdefault("source",    state.get("source"))
        new_state.setdefault("symptom",   state.get("symptom"))
        new_state.setdefault("forum_url", state.get("forum_url"))

        # Safety net: if a URL was in the message but Groq didn't capture it, grab it now
        url_in_msg = _extract_url(message)
        if url_in_msg and not new_state.get("forum_url"):
            new_state["forum_url"] = url_in_msg
            if not new_state.get("source"):
                new_state["source"] = "custom_forum"

        # If bot_message empty, generate deterministic fallback
        if not bot_message.strip():
            bot_message = _fallback_question(new_state)

        # Hard guard: mandatory fields filled → always READY
        # For custom_forum, also require forum_url
        if new_state.get("medicine") and new_state.get("source"):
            if new_state["source"] == "custom_forum" and not new_state.get("forum_url"):
                bot_message = _fallback_question(new_state)
            else:
                bot_message = READY_SIGNAL

        return new_state, bot_message

    except Exception as e:
        logger.error(f"[chat_manager] Groq call failed: {e}")
        return state, _fallback_question(state)


