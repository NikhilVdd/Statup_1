import json
import os
import urllib.error
import urllib.request


DEFAULT_SUGGESTION = {
    "suggested_response": "Ask one focused discovery question, then connect the answer to a clear business outcome.",
    "objection_detected": "None",
    "sentiment": "Neutral",
    "close_probability": 42,
    "call_health": "Stable",
    "next_action": "Ask a discovery question",
    "customer_intent": "Exploring fit",
    "urgency_level": "Medium",
    "key_moment": "Discovery is underway.",
    "buying_signal": "None",
    "scheduling_intent": False,
    "suggested_meeting_title": "",
    "suggested_meeting_time": "",
    "suggested_meeting_agenda": "",
}


def ai_provider_status():
    provider = os.getenv("AI_PROVIDER", "auto").lower()
    has_key = bool(os.getenv("OPENAI_API_KEY"))
    model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

    if provider == "mock":
        return {"mode": "mock", "label": "Mock AI", "model": "keyword-engine", "enabled": False}

    if has_key:
        return {"mode": "openai", "label": "Real AI", "model": model, "enabled": True}

    return {"mode": "mock", "label": "Mock AI", "model": "keyword-engine", "enabled": False}


def build_ai_prompt(call_state):
    company = call_state.company_context or {}
    recent_lines = call_state.transcript[-10:]
    transcript = "\n".join(f"{line['speaker']}: {line['text']}" for line in recent_lines)

    company_context = {
        "company_name": company.get("company_name", ""),
        "project_name": company.get("project_name", ""),
        "contact_name": company.get("contact_name", ""),
        "deal_stage": company.get("deal_stage", ""),
        "product_or_service": company.get("product_or_service", ""),
        "pain_points": company.get("pain_points", ""),
        "notes": company.get("notes", ""),
    }

    return [
        {
            "role": "system",
            "content": (
                "You are Loading..., a real-time AI sales teleprompter for ethical, consent-based sales calls. "
                "Give concise, professional coaching that helps the salesperson respond to the buyer in the moment. "
                "Do not invent facts. Use the client context only when relevant. Avoid manipulative, deceptive, or "
                "high-pressure advice. Return only valid JSON."
            ),
        },
        {
            "role": "user",
            "content": json.dumps(
                {
                    "task": "Generate the next live teleprompter suggestion for the salesperson.",
                    "required_json_shape": DEFAULT_SUGGESTION,
                    "client_context": company_context,
                    "current_call_state": {
                        "latest_customer_message": call_state.latest_customer_message,
                        "latest_sales_rep_message": call_state.latest_sales_rep_message,
                        "detected_objections": call_state.detected_objections,
                        "close_probability": call_state.close_probability,
                        "sentiment": call_state.sentiment,
                        "call_health": call_state.call_health,
                    },
                    "recent_transcript": transcript,
                    "rules": [
                        "suggested_response must be one or two sentences the sales rep can say next.",
                        "close_probability must be a number from 0 to 100.",
                        "scheduling_intent must be true only when the buyer suggests scheduling, meeting, calendar, next week, or booking a time.",
                        "If scheduling_intent is true, fill suggested_meeting_title, suggested_meeting_time, and suggested_meeting_agenda.",
                        "Use sales language that is clear, calm, specific, and buyer-friendly.",
                    ],
                }
            ),
        },
    ]


def generate_openai_suggestion(call_state):
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return None

    base_url = os.getenv("OPENAI_API_BASE", "https://api.openai.com/v1").rstrip("/")
    model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    timeout = float(os.getenv("AI_REQUEST_TIMEOUT", "12"))

    payload = {
        "model": model,
        "messages": build_ai_prompt(call_state),
        "temperature": 0.35,
        "max_tokens": 700,
        "response_format": {"type": "json_object"},
    }

    request = urllib.request.Request(
        f"{base_url}/chat/completions",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = json.loads(response.read().decode("utf-8"))
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as error:
        raise RuntimeError(f"AI provider request failed: {error}") from error

    content = raw["choices"][0]["message"]["content"]
    parsed = json.loads(content)
    return normalize_suggestion(parsed)


def normalize_suggestion(value):
    suggestion = DEFAULT_SUGGESTION.copy()
    if isinstance(value, dict):
        suggestion.update({key: value.get(key, suggestion[key]) for key in suggestion})

    suggestion["suggested_response"] = str(suggestion["suggested_response"]).strip()
    suggestion["objection_detected"] = str(suggestion["objection_detected"] or "None")
    suggestion["sentiment"] = str(suggestion["sentiment"] or "Neutral")
    suggestion["call_health"] = str(suggestion["call_health"] or "Stable")
    suggestion["next_action"] = str(suggestion["next_action"] or "Ask a discovery question")
    suggestion["customer_intent"] = str(suggestion["customer_intent"] or "Exploring fit")
    suggestion["urgency_level"] = str(suggestion["urgency_level"] or "Medium")
    suggestion["key_moment"] = str(suggestion["key_moment"] or "Live sales moment captured.")
    suggestion["buying_signal"] = str(suggestion["buying_signal"] or "None")
    suggestion["suggested_meeting_title"] = str(suggestion["suggested_meeting_title"] or "")
    suggestion["suggested_meeting_time"] = str(suggestion["suggested_meeting_time"] or "")
    suggestion["suggested_meeting_agenda"] = str(suggestion["suggested_meeting_agenda"] or "")
    suggestion["scheduling_intent"] = bool(suggestion["scheduling_intent"])

    try:
        close_probability = int(float(suggestion["close_probability"]))
    except (TypeError, ValueError):
        close_probability = DEFAULT_SUGGESTION["close_probability"]
    suggestion["close_probability"] = max(0, min(100, close_probability))

    return suggestion
