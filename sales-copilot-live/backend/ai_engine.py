def generate_live_sales_suggestion(call_state):
    recent_text = call_state.recent_transcript_text()
    latest_customer = call_state.latest_customer_message.lower()

    suggestion = {
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

    if any(phrase in latest_customer for phrase in ["set up a meeting", "schedule", "calendar", "next week", "book a time"]):
        suggestion.update(
            {
                "suggested_response": (
                    "Perfect. I can send over a focused follow-up session. To make that useful, should we center "
                    "the meeting on live objection handling, rep onboarding, or proving ROI with your current workflow?"
                ),
                "objection_detected": "None",
                "sentiment": "Positive",
                "close_probability": 78,
                "call_health": "Strong",
                "next_action": "Confirm meeting scope",
                "customer_intent": "Ready to schedule",
                "urgency_level": "High",
                "key_moment": "Customer signaled scheduling intent.",
                "buying_signal": "Meeting request",
                "scheduling_intent": True,
                "suggested_meeting_title": "Loading... sales workflow demo",
                "suggested_meeting_time": "Next week, 30 minutes",
                "suggested_meeting_agenda": "Show live guidance, objection handling, and ROI workflow.",
            }
        )
    elif any(word in latest_customer for word in ["expensive", "price", "cost", "budget"]):
        suggestion.update(
            {
                "suggested_response": (
                    "I completely understand the price concern. A lot of teams feel that way at first, "
                    "but the value is in helping reps save time, handle objections better, and close more deals. "
                    "Would it help if I showed how this could pay for itself based on your current call volume?"
                ),
                "objection_detected": "Price concern",
                "sentiment": "Cautious",
                "close_probability": 48,
                "call_health": "At risk",
                "next_action": "Quantify ROI",
                "customer_intent": "Evaluating cost",
                "urgency_level": "Medium",
                "key_moment": "Customer raised a price objection.",
            }
        )
    elif any(phrase in latest_customer for phrase in ["think about it", "not sure", "need to think"]):
        suggestion.update(
            {
                "suggested_response": (
                    "That makes sense. Usually when someone says they need to think about it, there is one "
                    "specific concern behind it. Is it the timing, the budget, or confidence that the team will use it?"
                ),
                "objection_detected": "Hesitation",
                "sentiment": "Uncertain",
                "close_probability": 40,
                "call_health": "At risk",
                "next_action": "Uncover the real concern",
                "customer_intent": "Needs reassurance",
                "urgency_level": "Medium",
                "key_moment": "Customer signaled hesitation.",
            }
        )
    elif "competitor" in latest_customer:
        suggestion.update(
            {
                "suggested_response": (
                    "It is smart to compare options. The biggest difference to look for is whether the tool only "
                    "reports what happened after the call, or actively helps reps during the call. What matters most "
                    "to you in that comparison?"
                ),
                "objection_detected": "Competitor comparison",
                "sentiment": "Comparing options",
                "close_probability": 45,
                "call_health": "Needs differentiation",
                "next_action": "Differentiate live guidance",
                "customer_intent": "Vendor comparison",
                "urgency_level": "High",
                "key_moment": "Customer mentioned a competitor.",
            }
        )
    elif "need to see" in latest_customer or "show me" in latest_customer or "demo" in latest_customer:
        suggestion.update(
            {
                "suggested_response": (
                    "Absolutely. The best next step is to show this on a realistic call scenario. If I can show how "
                    "it flags objections and suggests responses live, would that help you decide whether it saves time?"
                ),
                "objection_detected": "Proof needed",
                "sentiment": "Interested but validating",
                "close_probability": 62,
                "call_health": "Promising",
                "next_action": "Offer a targeted demo",
                "customer_intent": "Wants proof",
                "urgency_level": "High",
                "key_moment": "Customer asked for proof or a demo.",
            }
        )
    elif "training new reps" in recent_text:
        suggestion.update(
            {
                "suggested_response": (
                    "That training gap is exactly where live guidance can help. New reps do not have to memorize "
                    "every objection path on day one because the system can coach them in the moment."
                ),
                "objection_detected": "None",
                "sentiment": "Engaged",
                "close_probability": 58,
                "call_health": "Promising",
                "next_action": "Tie value to ramp time",
                "customer_intent": "Solving onboarding pain",
                "urgency_level": "Medium",
                "key_moment": "Customer identified rep training as a pain point.",
            }
        )
    elif "follow-ups" in recent_text or "follow ups" in recent_text:
        suggestion.update(
            {
                "suggested_response": (
                    "Follow-ups are a great place to create leverage. Loading... can capture the important moments, "
                    "surface next steps, and help reps leave every call with a cleaner action plan."
                ),
                "objection_detected": "None",
                "sentiment": "Positive",
                "close_probability": 56,
                "call_health": "Stable",
                "next_action": "Emphasize workflow automation",
                "customer_intent": "Improving sales operations",
                "urgency_level": "Medium",
                "key_moment": "Customer named follow-ups as a workflow issue.",
            }
        )
    elif any(word in latest_customer for word in ["interested", "helpful", "sounds good", "like the idea"]):
        suggestion.update(
            {
                "suggested_response": (
                    "Great. Based on what you shared, the strongest use case is helping reps respond faster during "
                    "live calls. Should we map this to one team workflow and define what a successful pilot would prove?"
                ),
                "objection_detected": "None",
                "sentiment": "Positive",
                "close_probability": 72,
                "call_health": "Strong",
                "next_action": "Propose a pilot",
                "customer_intent": "Interested",
                "urgency_level": "High",
                "key_moment": "Customer showed buying interest.",
                "buying_signal": "Interest",
            }
        )

    return suggestion
