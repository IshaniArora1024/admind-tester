from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from datetime import datetime
from typing import Any

app = FastAPI(title="AdMind Action API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

REQUIRED_FIELDS = {
    "inline_text": ["app_name", "sponsored_label", "ad_text", "cta_label", "cta_url"],
    "text_voice_card": [
        "app_name", "sponsored_label", "voice_brief", "put_forth", "at_no_time",
        "card_title", "card_subtitle", "delivery_line",
        "cta_primary_label", "cta_primary_url", "cta_secondary_label",
    ],
    "mcp_transaction_card": [
        "app_name", "sponsored_label", "voice_brief", "put_forth", "at_no_time",
        "card_title", "card_variant", "card_price", "delivery_label", "cta_label",
        "mcp_endpoint", "mcp_tool", "product_sku", "quantity", "latency_sla_ms",
    ],
    "post_conv_chip": [
        "app_name", "sponsored_label", "section_label",
        "chip_label", "chip_icon", "cta_url", "slot_position",
    ],
    "predictive_push": [
        "app_name", "sponsored_label", "title", "body",
        "cta_label", "cta_url", "deadline_label", "trigger_reason",
    ],
    "mcp_tool_chip": [
        "app_name", "sponsored_label", "chip_label", "chip_icon",
        "mcp_endpoint", "mcp_tool", "context_params",
    ],
    "teaser_hook": ["app_name", "teaser_question", "quick_replies"],
}


def ts(app_name: str) -> str:
    return app_name.lower().replace(" ", "_") + "_" + datetime.utcnow().strftime("%Y%m%d%H%M%S")


def split_csv(value: str) -> list:
    return [item.strip() for item in value.split(",") if item.strip()]


def build_inline_text(inputs: dict) -> dict:
    return {
        "ad_id": f"inline_{ts(inputs['app_name'])}",
        "format": "inline_text",
        "serve": {
            "app_name": inputs["app_name"],
            "sponsored_label": inputs["sponsored_label"],
            "text": inputs["ad_text"],
            "cta_label": inputs["cta_label"],
            "cta_url": inputs["cta_url"],
        },
        "guard": {
            "frequency_cap_session": 1,
            "label": "Sponsored",
        },
    }


def build_text_voice_card(inputs: dict) -> dict:
    return {
        "ad_id": f"multimodal_{ts(inputs['app_name'])}",
        "format": "text_voice_card",
        "serve": {
            "app_name": inputs["app_name"],
            "sponsored_label": inputs["sponsored_label"],
            "voice_brief": inputs["voice_brief"],
            "put_forth": split_csv(inputs["put_forth"]),
            "at_no_time": split_csv(inputs["at_no_time"]),
            "card": {
                "title": inputs["card_title"],
                "subtitle": inputs["card_subtitle"],
                "delivery_line": inputs["delivery_line"],
                "cta_primary_label": inputs["cta_primary_label"],
                "cta_primary_url": inputs["cta_primary_url"],
                "cta_secondary_label": inputs["cta_secondary_label"],
            },
        },
        "guard": {
            "frequency_cap_session": 1,
            "do_not_repeat": True,
        },
    }


def build_mcp_transaction_card(inputs: dict) -> dict:
    return {
        "ad_id": f"transaction_{ts(inputs['app_name'])}",
        "format": "mcp_transaction_card",
        "fulfilment_depth": "full_transaction",
        "serve": {
            "app_name": inputs["app_name"],
            "sponsored_label": inputs["sponsored_label"],
            "voice_brief": inputs["voice_brief"],
            "put_forth": split_csv(inputs["put_forth"]),
            "at_no_time": split_csv(inputs["at_no_time"]),
            "card": {
                "title": inputs["card_title"],
                "variant": inputs["card_variant"],
                "price": inputs["card_price"],
                "delivery_label": inputs["delivery_label"],
                "cta_label": inputs["cta_label"],
            },
        },
        "action": {
            "advertiser_mcp": inputs["mcp_endpoint"],
            "mcp_tool": inputs["mcp_tool"],
            "mcp_params": {
                "product_sku": inputs["product_sku"],
                "quantity": int(inputs["quantity"]),
            },
        },
        "guard": {
            "frequency_cap_session": 1,
            "do_not_repeat": True,
            "latency_sla_ms": int(inputs["latency_sla_ms"]),
        },
    }


def build_post_conv_chip(inputs: dict) -> dict:
    return {
        "ad_id": f"chip_{ts(inputs['app_name'])}",
        "format": "post_conv_chip",
        "serve": {
            "app_name": inputs["app_name"],
            "sponsored_label": inputs["sponsored_label"],
            "section_label": inputs["section_label"],
            "sponsored_chip": {
                "label": inputs["chip_label"],
                "icon": inputs["chip_icon"],
                "cta_url": inputs["cta_url"],
                "slot_position": int(inputs["slot_position"]),
            },
        },
        "guard": {
            "frequency_cap_session": 1,
        },
    }


def build_predictive_push(inputs: dict) -> dict:
    return {
        "ad_id": f"push_{ts(inputs['app_name'])}",
        "format": "predictive_push",
        "serve": {
            "app_name": inputs["app_name"],
            "sponsored_label": inputs["sponsored_label"],
            "title": inputs["title"],
            "body": inputs["body"],
            "cta_label": inputs["cta_label"],
            "cta_url": inputs["cta_url"],
            "deadline_label": inputs["deadline_label"],
        },
        "trigger_reason": inputs["trigger_reason"],
        "guard": {
            "frequency_cap_per_trip": 1,
        },
    }


def build_mcp_tool_chip(inputs: dict) -> dict:
    return {
        "ad_id": f"tool_{ts(inputs['app_name'])}",
        "format": "mcp_tool_chip",
        "serve": {
            "app_name": inputs["app_name"],
            "sponsored_label": inputs["sponsored_label"],
            "chip_label": inputs["chip_label"],
            "chip_icon": inputs["chip_icon"],
        },
        "action": {
            "advertiser_mcp": inputs["mcp_endpoint"],
            "mcp_tool": inputs["mcp_tool"],
            "mcp_params_from_context": split_csv(inputs["context_params"]),
        },
        "guard": {
            "frequency_cap_session": 2,
        },
    }


def build_teaser_hook(inputs: dict) -> dict:
    return {
        "ad_id": f"teaser_{ts(inputs['app_name'])}",
        "format": "teaser_hook",
        "serve": {
            "app_name": inputs["app_name"],
            "teaser_question": inputs["teaser_question"],
            "quick_replies": split_csv(inputs["quick_replies"]),
            "on_positive_response": "skip_ad",
        },
        "guard": {
            "frequency_cap_session": 1,
            "skip_if_positive": True,
        },
    }


BUILDERS = {
    "inline_text": build_inline_text,
    "text_voice_card": build_text_voice_card,
    "mcp_transaction_card": build_mcp_transaction_card,
    "post_conv_chip": build_post_conv_chip,
    "predictive_push": build_predictive_push,
    "mcp_tool_chip": build_mcp_tool_chip,
    "teaser_hook": build_teaser_hook,
}

FORMATS_META = {
    "inline_text": {
        "display_name": "Inline Text Ad",
        "required_fields": [
            {"key": "app_name", "label": "App / Brand Name", "type": "text", "placeholder": "e.g. VIP Luggage"},
            {"key": "sponsored_label", "label": "Sponsored Label", "type": "text", "placeholder": "e.g. SPONSORED · VIP LUGGAGE"},
            {"key": "ad_text", "label": "Ad Text", "type": "textarea", "placeholder": "The exact sentence shown inline in the conversation"},
            {"key": "cta_label", "label": "CTA Button Label", "type": "text", "placeholder": "e.g. Shop now"},
            {"key": "cta_url", "label": "CTA URL", "type": "text", "placeholder": "https://..."},
        ],
    },
    "text_voice_card": {
        "display_name": "Multimodal Card",
        "required_fields": [
            {"key": "app_name", "label": "App / Brand Name", "type": "text", "placeholder": "e.g. MakeMyTrip"},
            {"key": "sponsored_label", "label": "Sponsored Label", "type": "text", "placeholder": "e.g. SPONSORED · MMT"},
            {"key": "voice_brief", "label": "Voice Brief", "type": "textarea", "placeholder": "One sentence instruction for the publisher's AI to speak"},
            {"key": "put_forth", "label": "Put Forth (comma-separated)", "type": "text", "placeholder": "e.g. ₹5,999 duo set, free delivery, 10% cashback"},
            {"key": "at_no_time", "label": "At No Time (comma-separated)", "type": "text", "placeholder": "e.g. cheapest, best in India"},
            {"key": "card_title", "label": "Card Title", "type": "text", "placeholder": "e.g. VIP Skybags Pro — Family Set"},
            {"key": "card_subtitle", "label": "Card Subtitle", "type": "text", "placeholder": "e.g. 78cm + 68cm hardcase · ₹5,999"},
            {"key": "delivery_line", "label": "Delivery Line", "type": "text", "placeholder": "e.g. Free delivery before departure"},
            {"key": "cta_primary_label", "label": "Primary CTA Label", "type": "text", "placeholder": "e.g. Shop now"},
            {"key": "cta_primary_url", "label": "Primary CTA URL", "type": "text", "placeholder": "https://..."},
            {"key": "cta_secondary_label", "label": "Secondary CTA Label", "type": "text", "placeholder": "e.g. Dismiss"},
        ],
    },
    "mcp_transaction_card": {
        "display_name": "MCP Transaction Card",
        "required_fields": [
            {"key": "app_name", "label": "App / Brand Name", "type": "text", "placeholder": "e.g. Amazon"},
            {"key": "sponsored_label", "label": "Sponsored Label", "type": "text", "placeholder": "e.g. SPONSORED · AMAZON"},
            {"key": "voice_brief", "label": "Voice Brief", "type": "textarea", "placeholder": "One sentence to prime the user before the card appears"},
            {"key": "put_forth", "label": "Put Forth (comma-separated)", "type": "text", "placeholder": "e.g. ₹3,499, free delivery before flight"},
            {"key": "at_no_time", "label": "At No Time (comma-separated)", "type": "text", "placeholder": "e.g. cheapest, best in India"},
            {"key": "card_title", "label": "Product Name", "type": "text", "placeholder": "e.g. Sony WH-1000XM5"},
            {"key": "card_variant", "label": "Variant", "type": "text", "placeholder": "e.g. Midnight Black"},
            {"key": "card_price", "label": "Price", "type": "text", "placeholder": "e.g. ₹24,990"},
            {"key": "delivery_label", "label": "Delivery Label", "type": "text", "placeholder": "e.g. Arriving tomorrow by 8 PM"},
            {"key": "cta_label", "label": "Confirm Button Label", "type": "text", "placeholder": "e.g. Confirm & Pay ₹24,990"},
            {"key": "mcp_endpoint", "label": "MCP Endpoint URL", "type": "text", "placeholder": "https://api.advertiser.com/mcp"},
            {"key": "mcp_tool", "label": "MCP Tool Name", "type": "text", "placeholder": "e.g. place_order"},
            {"key": "product_sku", "label": "Product SKU", "type": "text", "placeholder": "e.g. SONY-WH1000XM5-BLK"},
            {"key": "quantity", "label": "Quantity", "type": "number", "placeholder": "1"},
            {"key": "latency_sla_ms", "label": "Latency SLA (ms)", "type": "number", "placeholder": "800"},
        ],
    },
    "post_conv_chip": {
        "display_name": "Category Chips",
        "required_fields": [
            {"key": "app_name", "label": "App / Brand Name", "type": "text", "placeholder": "e.g. Nykaa"},
            {"key": "sponsored_label", "label": "Sponsored Label", "type": "text", "placeholder": "e.g. SPONSORED · NYKAA"},
            {"key": "section_label", "label": "Section Label", "type": "text", "placeholder": "e.g. Before you go — essentials"},
            {"key": "chip_label", "label": "Chip Label", "type": "text", "placeholder": "e.g. Skincare — Nykaa"},
            {"key": "chip_icon", "label": "Chip Icon", "type": "text", "placeholder": "e.g. health"},
            {"key": "cta_url", "label": "CTA URL", "type": "text", "placeholder": "https://..."},
            {"key": "slot_position", "label": "Slot Position", "type": "number", "placeholder": "0"},
        ],
    },
    "predictive_push": {
        "display_name": "Predictive Push",
        "required_fields": [
            {"key": "app_name", "label": "App / Brand Name", "type": "text", "placeholder": "e.g. PhonePe"},
            {"key": "sponsored_label", "label": "Sponsored Label", "type": "text", "placeholder": "e.g. SPONSORED · PHONEPE"},
            {"key": "title", "label": "Notification Title", "type": "text", "placeholder": "e.g. Packing time?"},
            {"key": "body", "label": "Notification Body", "type": "textarea", "placeholder": "e.g. VIP's family set is ₹5,999 — free delivery before your flight."},
            {"key": "cta_label", "label": "CTA Label", "type": "text", "placeholder": "e.g. View deal"},
            {"key": "cta_url", "label": "CTA URL", "type": "text", "placeholder": "https://..."},
            {"key": "deadline_label", "label": "Deadline Label", "type": "text", "placeholder": "e.g. Last delivery date: May 20"},
            {"key": "trigger_reason", "label": "Trigger Reason", "type": "text", "placeholder": "e.g. days_before_departure:8"},
        ],
    },
    "mcp_tool_chip": {
        "display_name": "MCP Tool Chip",
        "required_fields": [
            {"key": "app_name", "label": "App / Brand Name", "type": "text", "placeholder": "e.g. Airbnb"},
            {"key": "sponsored_label", "label": "Sponsored Label", "type": "text", "placeholder": "e.g. SPONSORED · AIRBNB"},
            {"key": "chip_label", "label": "Chip Label", "type": "text", "placeholder": "e.g. Check Airbnb for my dates"},
            {"key": "chip_icon", "label": "Chip Icon", "type": "text", "placeholder": "e.g. hotel"},
            {"key": "mcp_endpoint", "label": "MCP Endpoint URL", "type": "text", "placeholder": "https://api.airbnb.com/mcp"},
            {"key": "mcp_tool", "label": "MCP Tool Name", "type": "text", "placeholder": "e.g. check_availability"},
            {"key": "context_params", "label": "Context Params (comma-separated)", "type": "text", "placeholder": "e.g. travel_dates, destination_city"},
        ],
    },
    "teaser_hook": {
        "display_name": "Teaser Hook",
        "required_fields": [
            {"key": "app_name", "label": "App / Brand Name", "type": "text", "placeholder": "e.g. Zomato"},
            {"key": "teaser_question", "label": "Teaser Question", "type": "text", "placeholder": "e.g. Got dinner sorted for tonight?"},
            {"key": "quick_replies", "label": "Quick Replies (comma-separated)", "type": "text", "placeholder": "e.g. Yes sorted, Not yet, Just browsing"},
        ],
    },
}


class ActionRequest(BaseModel):
    format: str
    inputs: dict[str, Any]


@app.get("/")
def root():
    return {
        "name": "AdMind Action API",
        "version": "1.0.0",
        "status": "running",
        "port": 8001,
        "endpoints": {
            "POST /v1/action": "Fill inputs into a format template and return final payload",
            "GET /v1/formats": "List all 7 formats and their required input fields",
        },
    }


@app.get("/v1/formats")
def get_formats():
    return {"formats": FORMATS_META}


@app.post("/v1/action")
def post_action(body: ActionRequest):
    fmt = body.format
    if fmt not in REQUIRED_FIELDS:
        raise HTTPException(
            status_code=400,
            detail={"error": "Unknown format", "valid_formats": list(REQUIRED_FIELDS.keys())},
        )

    missing = [f for f in REQUIRED_FIELDS[fmt] if f not in body.inputs or body.inputs[f] is None or str(body.inputs[f]).strip() == ""]
    if missing:
        raise HTTPException(
            status_code=400,
            detail={"error": "Missing fields", "missing": missing},
        )

    return BUILDERS[fmt](body.inputs)
