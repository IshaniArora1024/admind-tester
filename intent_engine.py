import json
import re
from typing import List, Optional

from config import GEMINI_API_KEY
from models import ConversationMessage

INTENT_KEYWORDS = {
    "luggage_needed": [
        "luggage", "suitcase", "bag", "packing", "pack",
        "carry", "baggage", "trolley", "hardcase",
    ],
    "flight_booked": [
        "booked", "confirmed", "ticket", "flight confirmed",
        "booking confirmed", "seats confirmed", "itinerary",
    ],
    "trip_planning": [
        "trip", "travel", "journey", "vacation", "holiday",
        "visiting", "going to", "flying to", "travelling",
    ],
    "purchase_intent": [
        "buy", "order", "purchase", "get one", "want one",
        "how much", "price", "cost", "where to buy",
    ],
    "hotel_needed": [
        "hotel", "stay", "accommodation", "airbnb", "resort",
        "where to stay", "book a room",
    ],
    "skincare_needed": [
        "sunscreen", "spf", "sunburn", "skin", "lotion",
        "beach", "tan", "moisturiser",
    ],
    "food_ordering": [
        "hungry", "food", "eat", "order food", "restaurant",
        "delivery", "zomato", "swiggy",
    ],
    "conversation_ended": [
        "thank you", "thanks", "great", "perfect", "all set",
        "that is all", "bye", "done", "sorted",
    ],
}


def _keyword_in_text(keyword: str, text: str) -> bool:
    # Use word boundaries so "eat" doesn't match inside "weather"
    return bool(re.search(r"\b" + re.escape(keyword) + r"\b", text))


def detect_intent_gemini(conversation: List[ConversationMessage]) -> Optional[dict]:
    try:
        import google.generativeai as genai

        genai.configure(api_key=GEMINI_API_KEY)
        model = genai.GenerativeModel("gemini-1.5-flash")

        formatted = "\n".join(
            f"{msg.role.upper()}: {msg.content}" for msg in conversation
        )

        prompt = (
            "You are an intent detection engine for an ad platform.\n"
            "Analyse this conversation and return ONLY a JSON object.\n"
            "No explanation, no markdown, just raw JSON.\n\n"
            "Return this exact structure:\n"
            "{\n"
            '  "primary_intent": one of [\n'
            '    "luggage_needed",\n'
            '    "flight_booked",\n'
            '    "hotel_needed",\n'
            '    "packing_discussion",\n'
            '    "trip_planning",\n'
            '    "purchase_intent",\n'
            '    "conversation_ended",\n'
            '    "skincare_needed",\n'
            '    "food_ordering",\n'
            '    "none"\n'
            "  ],\n"
            '  "confidence": float between 0 and 1,\n'
            '  "signals": [list of words/phrases that led to this intent],\n'
            '  "trip_details": {\n'
            '    "destination": string or null,\n'
            '    "duration_days": int or null,\n'
            '    "travellers": int or null,\n'
            '    "departure_date": string or null\n'
            "  },\n"
            '  "conversation_ended": boolean\n'
            "}\n\n"
            "Conversation to analyse:\n"
            f"{formatted}"
        )

        response = model.generate_content(prompt)
        raw = response.text.strip()

        raw = re.sub(r"^```(?:json)?", "", raw).strip()
        raw = re.sub(r"```$", "", raw).strip()

        return json.loads(raw)

    except Exception as e:
        print(f"[AdMind] Gemini intent detection failed: {e}")
        return None


def detect_intent_keywords(conversation: List[ConversationMessage]) -> dict:
    full_text = " ".join(msg.content for msg in conversation).lower()

    best_intent = "none"
    best_count = 0
    best_confidence = 0.0

    for intent, keywords in INTENT_KEYWORDS.items():
        count = sum(1 for kw in keywords if _keyword_in_text(kw, full_text))
        if count > best_count:
            best_count = count
            best_intent = intent
            best_confidence = round(count / len(keywords), 2)

    signals = [
        kw
        for kw in INTENT_KEYWORDS.get(best_intent, [])
        if _keyword_in_text(kw, full_text)
    ]

    conversation_ended = any(
        _keyword_in_text(kw, full_text) for kw in INTENT_KEYWORDS["conversation_ended"]
    )

    return {
        "primary_intent": best_intent,
        "confidence": best_confidence,
        "signals": signals,
        "trip_details": {
            "destination": None,
            "duration_days": None,
            "travellers": None,
            "departure_date": None,
        },
        "conversation_ended": conversation_ended,
    }


def detect_intent(conversation: List[ConversationMessage], use_gemini: bool = True) -> dict:
    if use_gemini and GEMINI_API_KEY:
        result = detect_intent_gemini(conversation)
        if result and result.get("confidence", 0) >= 0.6:
            result["method"] = "gemini"
            return result

    result = detect_intent_keywords(conversation)
    result["method"] = "keywords"
    return result
