from datetime import datetime, timezone
from models import AnalyseRequest


def build_payload(
    campaign: dict,
    format_name: str,
    intent: dict,
    request: AnalyseRequest,
) -> dict:
    format_config = campaign.get("formats", {}).get(format_name, {})
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S%f")

    action = format_config.get("action")

    payload = {
        "ad_id": f"{campaign.get('campaign_id', 'unknown')}_{format_name}_{timestamp}",
        "format": format_name,
        "serve": format_config.get("serve", {}),
        "guard": format_config.get("guard", {}),
        "meta": {
            "advertiser": campaign.get("advertiser", ""),
            "triggered_by": intent.get("primary_intent", "none"),
            "confidence": intent.get("confidence", 0.0),
            "method": intent.get("method", "keywords"),
            "trip_details": intent.get("trip_details", {}),
        },
    }

    if action is not None:
        payload["action"] = action

    return payload
