from datetime import datetime, timezone
from uuid import uuid4


class CallState:
    def __init__(self):
        self.call_id = str(uuid4())
        self.is_active = False
        self.started_at = None
        self.ended_at = None
        self.transcript = []
        self.latest_customer_message = ""
        self.latest_sales_rep_message = ""
        self.detected_objections = []
        self.suggestions = []
        self.close_probability = 35
        self.sentiment = "Neutral"
        self.call_health = "Stable"
        self.scheduling_intent = False
        self.key_moments = []
        self.company_id = None
        self.meeting_id = None
        self.company_context = {}

    def start(self):
        self.is_active = True
        self.started_at = datetime.now(timezone.utc).isoformat()
        self.ended_at = None

    def set_context(self, company=None, meeting_id=None):
        self.company_context = company or {}
        self.company_id = self.company_context.get("id")
        self.meeting_id = meeting_id

    def stop(self):
        self.is_active = False
        self.ended_at = datetime.now(timezone.utc).isoformat()

    def add_transcript_line(self, speaker, text):
        entry = {
            "speaker": speaker,
            "text": text,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        self.transcript.append(entry)

        if speaker.lower().startswith("customer"):
            self.latest_customer_message = text
        else:
            self.latest_sales_rep_message = text

    def add_suggestion(self, suggestion):
        self.suggestions.append(suggestion)
        self.close_probability = suggestion.get("close_probability", self.close_probability)
        self.sentiment = suggestion.get("sentiment", self.sentiment)
        self.call_health = suggestion.get("call_health", self.call_health)
        self.scheduling_intent = suggestion.get("scheduling_intent", self.scheduling_intent)

        objection = suggestion.get("objection_detected")
        if objection and objection != "None" and objection not in self.detected_objections:
            self.detected_objections.append(objection)

        key_moment = suggestion.get("key_moment")
        if key_moment and key_moment != "None":
            self.key_moments.append(key_moment)

    def recent_transcript_text(self, limit=6):
        recent_lines = self.transcript[-limit:]
        return " ".join(line["text"] for line in recent_lines).lower()

    def to_dict(self):
        return {
            "call_id": self.call_id,
            "is_active": self.is_active,
            "started_at": self.started_at,
            "ended_at": self.ended_at,
            "transcript": self.transcript,
            "latest_customer_message": self.latest_customer_message,
            "latest_sales_rep_message": self.latest_sales_rep_message,
            "detected_objections": self.detected_objections,
            "suggestions": self.suggestions,
            "close_probability": self.close_probability,
            "sentiment": self.sentiment,
            "call_health": self.call_health,
            "scheduling_intent": self.scheduling_intent,
            "key_moments": self.key_moments,
            "company_id": self.company_id,
            "meeting_id": self.meeting_id,
            "company_context": self.company_context,
        }
