def build_call_summary(call_state):
    latest_suggestion = call_state.suggestions[-1] if call_state.suggestions else {}
    company = call_state.company_context or {}
    company_name = company.get("company_name", "this client")
    return {
        "headline": f"Call completed for {company_name}",
        "total_transcript_lines": len(call_state.transcript),
        "detected_objections": call_state.detected_objections or ["None"],
        "final_sentiment": call_state.sentiment,
        "final_close_probability": call_state.close_probability,
        "final_call_health": call_state.call_health,
        "scheduling_intent": call_state.scheduling_intent,
        "recommended_next_action": latest_suggestion.get("next_action", "Schedule a follow-up"),
        "key_moments": call_state.key_moments[-5:],
        "buying_signal": latest_suggestion.get("buying_signal", "None"),
        "suggested_follow_up_email": (
            f"Hi {company.get('contact_name', 'there')}, thanks for the conversation today. "
            f"Based on what we discussed around {company.get('pain_points', 'your sales workflow')}, "
            "I would suggest a focused follow-up to review the next steps and confirm fit."
        ),
    }
