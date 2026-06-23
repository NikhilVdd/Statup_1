def build_call_summary(call_state):
    latest_suggestion = call_state.suggestions[-1] if call_state.suggestions else {}
    return {
        "headline": "Demo call completed",
        "total_transcript_lines": len(call_state.transcript),
        "detected_objections": call_state.detected_objections or ["None"],
        "final_sentiment": call_state.sentiment,
        "final_close_probability": call_state.close_probability,
        "recommended_next_action": latest_suggestion.get("next_action", "Schedule a follow-up"),
        "key_moments": call_state.key_moments[-5:],
    }
