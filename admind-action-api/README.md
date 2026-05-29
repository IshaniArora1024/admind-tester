# AdMind Action API

## What This Is
This API stores fixed templates for all 7 AdMind ad formats.
You send the content (brand name, price, text etc.) and it returns
the complete final payload ready for the publisher's app to render.

## Run It
```
pip install -r requirements.txt
uvicorn main:app --reload --port 8001
```
Open: http://localhost:8001/docs

## Test Cases — paste these into /docs

### Format 1 — Inline Text
POST /v1/action
```json
{
  "format": "inline_text",
  "inputs": {
    "app_name": "VIP Luggage",
    "sponsored_label": "SPONSORED · VIP LUGGAGE",
    "ad_text": "VIP's 78cm hardcase is ₹3,499 with free 48h delivery and 10% MMT cashback.",
    "cta_label": "Shop VIP Luggage",
    "cta_url": "https://vip.in/mmt?ref=inline"
  }
}
```
Expected: inline_text payload with text and CTA filled in

### Format 2 — Multimodal Card
POST /v1/action
```json
{
  "format": "text_voice_card",
  "inputs": {
    "app_name": "MakeMyTrip",
    "sponsored_label": "SPONSORED · MMT",
    "voice_brief": "Family of 5 just booked flights — mention luggage set. One sentence.",
    "put_forth": "₹5,999 duo set, free delivery before departure, 10% MMT cashback",
    "at_no_time": "cheapest, best in India",
    "card_title": "VIP Skybags Pro — Family Set",
    "card_subtitle": "78cm + 68cm hardcase · ₹5,999",
    "delivery_line": "Free delivery before departure",
    "cta_primary_label": "Shop now",
    "cta_primary_url": "https://vip.in/mmt?ref=card",
    "cta_secondary_label": "Dismiss"
  }
}
```
Expected: text_voice_card payload with card filled in and put_forth/at_no_time as lists

### Format 3 — MCP Transaction Card
POST /v1/action
```json
{
  "format": "mcp_transaction_card",
  "inputs": {
    "app_name": "Amazon",
    "sponsored_label": "SPONSORED · AMAZON",
    "voice_brief": "User wants headphones — mention Sony WH-1000XM5. Ask if they want to order.",
    "put_forth": "₹24,990, Prime delivery tomorrow",
    "at_no_time": "cheapest, best ever",
    "card_title": "Sony WH-1000XM5",
    "card_variant": "Midnight Black",
    "card_price": "₹24,990",
    "delivery_label": "Arriving tomorrow by 8 PM",
    "cta_label": "Confirm & Pay ₹24,990",
    "mcp_endpoint": "https://api.amazon.in/mcp",
    "mcp_tool": "place_order",
    "product_sku": "SONY-WH1000XM5-BLK",
    "quantity": "1",
    "latency_sla_ms": "800"
  }
}
```
Expected: mcp_transaction_card payload with action block filled in

### Format 4 — Category Chips
POST /v1/action
```json
{
  "format": "post_conv_chip",
  "inputs": {
    "app_name": "Nykaa",
    "sponsored_label": "SPONSORED · NYKAA",
    "section_label": "Before you go — essentials",
    "chip_label": "Skincare — Nykaa",
    "chip_icon": "health",
    "cta_url": "https://nykaa.com?ref=admind",
    "slot_position": "0"
  }
}
```
Expected: post_conv_chip payload with sponsored_chip filled in

### Format 5 — Predictive Push
POST /v1/action
```json
{
  "format": "predictive_push",
  "inputs": {
    "app_name": "PhonePe",
    "sponsored_label": "SPONSORED · PHONEPE",
    "title": "Trip coming up?",
    "body": "Get travel insurance for ₹199 — covers cancellation and baggage loss.",
    "cta_label": "View deal",
    "cta_url": "https://phonepe.com/insurance?ref=admind",
    "deadline_label": "Offer valid until departure",
    "trigger_reason": "days_before_departure:6"
  }
}
```
Expected: predictive_push payload with notification fields filled in

### Format 6 — MCP Tool Chip
POST /v1/action
```json
{
  "format": "mcp_tool_chip",
  "inputs": {
    "app_name": "Airbnb",
    "sponsored_label": "SPONSORED · AIRBNB",
    "chip_label": "Check Airbnb for my dates",
    "chip_icon": "hotel",
    "mcp_endpoint": "https://api.airbnb.com/mcp",
    "mcp_tool": "check_availability",
    "context_params": "travel_dates, destination_city"
  }
}
```
Expected: mcp_tool_chip payload with action block and context_params as list

### Format 7 — Teaser Hook
POST /v1/action
```json
{
  "format": "teaser_hook",
  "inputs": {
    "app_name": "Zomato",
    "teaser_question": "Got dinner sorted for tonight?",
    "quick_replies": "Yes sorted, Not yet, Just browsing"
  }
}
```
Expected: teaser_hook payload with quick_replies as list

### Error Test — Missing field
POST /v1/action
```json
{
  "format": "inline_text",
  "inputs": {
    "app_name": "VIP Luggage"
  }
}
```
Expected: 400 error listing missing fields

### Error Test — Invalid format
POST /v1/action
```json
{
  "format": "unknown_format",
  "inputs": {}
}
```
Expected: 400 error with list of valid format names
