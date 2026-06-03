import json
from datetime import datetime, timezone
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from campaign_matcher import load_all_campaigns, match_campaign
from config import ADMIND_MASTER_KEY, CLICKS_PATH, IMPRESSIONS_PATH, LOG_CLICKS, LOG_IMPRESSIONS
from intent_engine import detect_intent
from models import AdPayloadResponse, AnalyseRequest, ClickRequest, ImpressionRequest
from payload_builder import build_payload

app = FastAPI(
    title="AdMind API",
    description="AI-native ad platform API. Returns intelligent ad payloads based on conversation context.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup_event():
    print("AdMind API started. Docs at http://localhost:8000/docs")
    campaigns = load_all_campaigns()
    print(f"[AdMind] Loaded {len(campaigns)} active campaign(s).")


def validate_publisher_key(key: str) -> bool:
    # TODO: Replace with real database lookup
    return key == ADMIND_MASTER_KEY or key.startswith("pub_")


@app.get("/", tags=["Health"])
def root():
    return {
        "name": "AdMind API",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs",
        "endpoints": ["/v1/analyse", "/v1/impression", "/v1/click"],
    }


@app.post("/v1/analyse", response_model=AdPayloadResponse, tags=["Core"])
def analyse(request: AnalyseRequest):
    """
    Analyse a conversation and return the most relevant ad payload.

    This is the main endpoint of the AdMind SDK. The publisher sends the last
    N messages of a conversation along with optional signals (trip_confirmed,
    days_before_departure, conversation_ended). The API:

    1. Validates the publisher key.
    2. Detects the user's intent using Gemini (with keyword fallback).
    3. Matches the intent against active advertiser campaigns.
    4. Returns the best ad format payload, or null if no match.

    Example request body:
    ```json
    {
      "conversation": [
        {"role": "user", "content": "I just booked flights to Goa for 5 people"},
        {"role": "assistant", "content": "Great! Goa in May is lovely."},
        {"role": "user", "content": "I need to sort out luggage for everyone"}
      ],
      "user_id": "test_user_001",
      "publisher_key": "admind_test_key_123",
      "requested_format": "inline_text"
    }
    ```

    `requested_format` is optional. When provided, the API returns that specific format
    (if enabled for the matched campaign) instead of auto-selecting one. Valid values:
    `teaser_hook`, `inline_text`, `text_voice_card`, `mcp_transaction_card`,
    `post_conv_chip`, `predictive_push`, `mcp_tool_chip`.
    Omit to let the API pick the best format automatically.
    """
    if not validate_publisher_key(request.publisher_key):
        raise HTTPException(
            status_code=401,
            detail={"error": "Invalid publisher key", "code": "ADMIND_001"},
        )

    if not request.conversation:
        raise HTTPException(
            status_code=400,
            detail={"error": "Conversation cannot be empty", "code": "ADMIND_002"},
        )

    conversation = request.conversation[-10:]

    intent = detect_intent(conversation)
    print(
        f"[AdMind] Intent detected: {intent.get('primary_intent')} "
        f"(confidence: {intent.get('confidence')}, method: {intent.get('method')})"
    )

    match = match_campaign(intent, request)

    if match is None:
        print(f"[AdMind] No campaign matched for user {request.user_id}. Returning null.")
        return AdPayloadResponse(
            ad=None,
            format=None,
            triggered_by=None,
            session_id=request.session_id,
        )

    campaign, format_name = match
    print(f"[AdMind] Campaign matched: {campaign.get('advertiser')} → {format_name}")

    payload = build_payload(campaign, format_name, intent, request)
    print(f"[AdMind] Returning: {format_name} ad for {request.user_id}")

    return AdPayloadResponse(
        ad=payload,
        format=format_name,
        triggered_by=intent.get("primary_intent"),
        session_id=request.session_id,
    )


@app.post("/v1/impression", tags=["Tracking"])
def log_impression(request: ImpressionRequest):
    """Log that an ad was shown to a user."""
    if not validate_publisher_key(request.publisher_key):
        raise HTTPException(
            status_code=401,
            detail={"error": "Invalid publisher key", "code": "ADMIND_001"},
        )

    if LOG_IMPRESSIONS:
        entry = {
            "ad_id": request.ad_id,
            "user_id": request.user_id,
            "format": request.format,
            "publisher_key": request.publisher_key,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        with open(IMPRESSIONS_PATH, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry) + "\n")

    return {"logged": True, "ad_id": request.ad_id}


@app.post("/v1/click", tags=["Tracking"])
def log_click(request: ClickRequest):
    """Log that a user tapped the CTA on an ad."""
    if not validate_publisher_key(request.publisher_key):
        raise HTTPException(
            status_code=401,
            detail={"error": "Invalid publisher key", "code": "ADMIND_001"},
        )

    if LOG_CLICKS:
        entry = {
            "ad_id": request.ad_id,
            "user_id": request.user_id,
            "format": request.format,
            "publisher_key": request.publisher_key,
            "cta_url": request.cta_url,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        with open(CLICKS_PATH, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry) + "\n")

    return {"logged": True, "ad_id": request.ad_id}
