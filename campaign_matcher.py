import json
import time
import warnings
from pathlib import Path
from typing import List, Optional, Tuple

from config import CAMPAIGNS_DIR
from models import AnalyseRequest

_campaign_cache: List[dict] = []
_cache_loaded_at: float = 0.0
_CACHE_TTL_SECONDS = 60

FORMAT_PRIORITY = [
    "mcp_transaction_card",
    "teaser_hook",
    "text_voice_card",
    "predictive_push",
    "mcp_tool_chip",
    "post_conv_chip",
    "inline_text",
]


def load_all_campaigns() -> List[dict]:
    global _campaign_cache, _cache_loaded_at

    now = time.time()
    if _campaign_cache and (now - _cache_loaded_at) < _CACHE_TTL_SECONDS:
        return _campaign_cache

    campaigns = []
    campaigns_path = Path(CAMPAIGNS_DIR)

    for json_file in campaigns_path.glob("*.json"):
        try:
            with open(json_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            if data.get("active", False):
                campaigns.append(data)
        except json.JSONDecodeError as e:
            warnings.warn(f"[AdMind] Skipping malformed campaign file {json_file.name}: {e}")
        except Exception as e:
            warnings.warn(f"[AdMind] Could not load campaign file {json_file.name}: {e}")

    _campaign_cache = campaigns
    _cache_loaded_at = now
    return campaigns


def _get_effective_intents(intent: dict, request: AnalyseRequest) -> List[str]:
    """
    Build a prioritised list of intents to try: detected intent first,
    then intents inferred from explicit publisher signals.
    """
    primary = intent.get("primary_intent", "none")
    intents: List[str] = []

    if primary != "none":
        intents.append(primary)

    if request.trip_confirmed and "flight_booked" not in intents:
        intents.append("flight_booked")

    if request.days_before_departure is not None and request.days_before_departure <= 8:
        for extra in ("trip_planning", "flight_booked"):
            if extra not in intents:
                intents.append(extra)

    if (
        request.conversation_ended or intent.get("conversation_ended", False)
    ) and "conversation_ended" not in intents:
        intents.append("conversation_ended")

    if not intents:
        intents.append("none")

    return intents


def _has_real_detected_intent(intent: dict) -> bool:
    """True when the AI/keywords actually detected an intent (not just signal-derived)."""
    return intent.get("primary_intent", "none") not in ("none", None)


def _format_is_eligible(
    format_name: str,
    format_config: dict,
    effective_intent: str,
    intent: dict,
    request: AnalyseRequest,
) -> bool:
    if not format_config.get("enabled", False):
        return False

    trigger_intents = format_config.get("trigger_intents", [])
    if effective_intent not in trigger_intents:
        return False

    # Intrusive formats require a real conversation-detected intent,
    # not just a signal like days_before_departure.
    if format_name in ("teaser_hook", "text_voice_card") and not _has_real_detected_intent(intent):
        return False

    if format_name == "post_conv_chip":
        if not (request.conversation_ended or intent.get("conversation_ended", False)):
            return False

    if format_name == "predictive_push":
        days = request.days_before_departure
        if days is None or days > 8:
            return False

    if format_name == "mcp_transaction_card":
        real_intent = intent.get("primary_intent", "none")
        if effective_intent != "purchase_intent" and real_intent != "purchase_intent":
            return False

    return True


def match_campaign(
    intent: dict, request: AnalyseRequest
) -> Optional[Tuple[dict, str]]:
    campaigns = load_all_campaigns()
    effective_intents = _get_effective_intents(intent, request)

    if request.requested_format:
        # Developer explicitly requested a format — serve it directly if the campaign matches
        for campaign in campaigns:
            target_intents = campaign.get("target_intents", [])
            if not any(ei in target_intents for ei in effective_intents):
                continue
            format_config = campaign.get("formats", {}).get(request.requested_format)
            if format_config and format_config.get("enabled", False):
                return campaign, request.requested_format
        return None

    for campaign in campaigns:
        target_intents = campaign.get("target_intents", [])
        matching_intents = [ei for ei in effective_intents if ei in target_intents]

        if not matching_intents:
            continue

        formats = campaign.get("formats", {})

        for format_name in FORMAT_PRIORITY:
            format_config = formats.get(format_name)
            if format_config is None:
                continue

            for eff_intent in matching_intents:
                if _format_is_eligible(format_name, format_config, eff_intent, intent, request):
                    return campaign, format_name

    return None
