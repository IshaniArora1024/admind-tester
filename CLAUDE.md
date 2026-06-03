# AdMind API — Claude Session Context

## What this project is

AdMind is a **Python FastAPI backend** that acts as an AI-native ad platform. It sits inside a developer's chat application, analyses conversation context, detects user intent, and returns a targeted ad payload in the format the developer requests. The developer integrates it with two lines of code — send conversation, receive ad.

Owner: ministryoftruth.bhai@gmail.com  
Local dev: `uvicorn main:app --reload` → `http://localhost:8000`  
Docs (Swagger): `http://localhost:8000/docs`  
HTML tester (separate, do not modify): `https://admind-tester-1.onrender.com` — points to localhost, used as a demo/reference tool for another website.  
Backend deployment target: Render (`render.yaml` is already configured at project root).

---

## Project structure

```
admind-api/
├── main.py               # FastAPI app, 4 endpoints, CORS, auth
├── models.py             # Pydantic request/response schemas
├── intent_engine.py      # Gemini API + keyword fallback intent detection
├── campaign_matcher.py   # Campaign loading, matching, format selection
├── payload_builder.py    # Builds final ad payload dict
├── config.py             # Env vars, log paths
├── render.yaml           # Render deployment config
├── requirements.txt      # Python dependencies
├── .env                  # GEMINI_API_KEY, ADMIND_MASTER_KEY (never commit)
├── .env.example          # Template
├── campaigns/            # Advertiser campaign JSON files
│   ├── vip_luggage.json  # Active campaign (primary example)
│   └── sample_*.json     # Inactive reference campaigns
└── logs/
    ├── impressions.jsonl
    └── clicks.jsonl
```

---

## API endpoints

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/` | Health check |
| POST | `/v1/analyse` | Main endpoint — detect intent, return ad payload |
| POST | `/v1/impression` | Log that an ad was shown |
| POST | `/v1/click` | Log that a user clicked the CTA |
| GET | `/docs` | Auto-generated Swagger UI |

### POST /v1/analyse — request schema

```python
class AnalyseRequest(BaseModel):
    conversation: List[ConversationMessage]   # required — full chat history
    user_id: str                              # required — caller's user ID
    publisher_key: str                        # required — auth key (pub_xxx)
    session_id: Optional[str] = None         # optional — chat session ID
    trip_confirmed: Optional[bool] = False   # signal: user confirmed a booking
    days_before_departure: Optional[int] = None  # signal: days until trip
    conversation_ended: Optional[bool] = False   # signal: chat is over
    requested_format: Optional[str] = None   # developer picks the ad format
```

`requested_format` is the key developer-facing field added in the latest session. When set, the API skips its auto-priority logic and serves that exact format (if enabled for the matched campaign). If omitted, the API auto-selects the best format.

### POST /v1/analyse — response schema

```json
{
  "ad": { ... },           // null if no campaign matched
  "format": "teaser_hook", // which format was served
  "triggered_by": "luggage_needed",
  "session_id": "..."
}
```

The `ad` object always has: `ad_id`, `format`, `serve` (content), `guard` (frequency caps), `meta` (advertiser, intent, confidence), and optionally `action` (MCP tool call params).

---

## Ad formats

The system supports 7 formats. `serve` content differs per format:

| Format | `serve` fields | When it triggers |
|--------|---------------|-----------------|
| `teaser_hook` | `teaser_question`, `quick_replies`, `on_negative_response` (card + voice_brief), `on_positive_response` | Trip planning, flight booked, luggage needed |
| `inline_text` | `text`, `cta_label`, `cta_url` | Luggage needed, packing discussion |
| `text_voice_card` | `voice_brief`, `put_forth`, `at_no_time`, `card` (title, subtitle, cta_primary, cta_secondary) | Flight booked, trip planning |
| `mcp_transaction_card` | `voice_brief`, `card` (title, variant, price, cta_label) + `action` (mcp_tool, mcp_params) | Purchase intent, flight booked |
| `post_conv_chip` | `section_label`, `sponsored_chip` (label, icon, cta_url, slot_position) | `conversation_ended: true` |
| `predictive_push` | `title`, `body`, `cta_label`, `cta_url`, `deadline_label` | `days_before_departure <= 8` |
| `mcp_tool_chip` | `chip_label`, `chip_icon` + `action` (mcp_tool, mcp_params_from_context) | Trip planning, flight booked |

Format priority when auto-selecting (highest to lowest):
`mcp_transaction_card` → `teaser_hook` → `text_voice_card` → `predictive_push` → `mcp_tool_chip` → `post_conv_chip` → `inline_text`

---

## Intent detection (intent_engine.py)

Two-tier system:
1. **Gemini 1.5 Flash** (primary) — sends conversation, gets JSON with `primary_intent`, `confidence`, `signals`, `trip_details`, `conversation_ended`. Used when confidence ≥ 0.6.
2. **Keyword fallback** — always available, matches 8 intents: `luggage_needed`, `flight_booked`, `trip_planning`, `purchase_intent`, `hotel_needed`, `skincare_needed`, `food_ordering`, `conversation_ended`.

Detected intents plus publisher signals (`trip_confirmed`, `days_before_departure`, `conversation_ended`) are combined into `effective_intents` in `_get_effective_intents()`.

---

## Campaign matching (campaign_matcher.py)

Key function: `match_campaign(intent, request) -> Optional[(campaign, format_name)]`

Flow:
1. Load all active campaigns from `campaigns/*.json` (60s cache)
2. Build `effective_intents` from detected intent + publisher signals
3. **If `request.requested_format` is set**: find a campaign whose `target_intents` overlap with `effective_intents`, check if that format is `enabled: true` → return it. Skip all eligibility guards.
4. **If no `requested_format`**: iterate `FORMAT_PRIORITY`, call `_format_is_eligible()` for each, return first match.

`_format_is_eligible()` enforces:
- Format must be `enabled: true`
- Detected intent must be in format's `trigger_intents`
- `teaser_hook` / `text_voice_card`: require real AI/keyword detected intent (not just signals)
- `post_conv_chip`: requires `conversation_ended`
- `predictive_push`: requires `days_before_departure <= 8`
- `mcp_transaction_card`: requires `purchase_intent`

---

## Campaign JSON schema

Live in `campaigns/`. Only files with `"active": true` are loaded.

```json
{
  "campaign_id": "vip_001",
  "advertiser": "VIP Luggage",
  "active": true,
  "category": "luggage",
  "target_intents": ["luggage_needed", "flight_booked", "trip_planning", ...],
  "formats": {
    "teaser_hook": {
      "enabled": true,
      "trigger_intents": ["trip_planning", "flight_booked", "luggage_needed"],
      "serve": { ... },
      "guard": { "frequency_cap_session": 1 },
      "action": { ... }
    }
  }
}
```

To add a new advertiser: create a new JSON file in `campaigns/`, set `"active": true`. No code changes needed — campaigns are hot-reloaded every 60 seconds.

---

## Auth / publisher keys

`validate_publisher_key()` in `main.py`:
- Accepts `ADMIND_MASTER_KEY` (env var, default: `admind_test_key_123`) for internal testing
- Accepts any key starting with `pub_` for developer publishers
- Returns 401 (`ADMIND_001`) otherwise
- TODO: Replace with real database lookup

To issue a key to a developer: share a string like `pub_devname_001` — no backend change needed yet.

---

## Environment variables

| Var | Default | Purpose |
|-----|---------|---------|
| `GEMINI_API_KEY` | (empty) | Google Gemini API key — falls back to keywords if missing |
| `ADMIND_MASTER_KEY` | `admind_test_key_123` | Internal test key |
| `LOG_IMPRESSIONS` | `true` | Write impressions to JSONL |
| `LOG_CLICKS` | `true` | Write clicks to JSONL |
| `CAMPAIGNS_DIR` | `campaigns` | Path to campaign JSON folder |
| `LOGS_DIR` | `logs` | Path to log output folder |

---

## Deployment (Render)

`render.yaml` is at the project root. Steps:
1. Push project to GitHub
2. Render → New → Web Service → connect repo
3. Render auto-detects `render.yaml`
4. Set `GEMINI_API_KEY` and `ADMIND_MASTER_KEY` in Render dashboard → Environment
5. API goes live at `https://admind-api.onrender.com`

Build: `pip install -r requirements.txt`  
Start: `uvicorn main:app --host 0.0.0.0 --port $PORT`

---

## Developer integration example

```python
import requests

BASE_URL = "https://admind-api.onrender.com"
PUBLISHER_KEY = "pub_devname_001"

# Call on every user message turn
def get_ad(conversation, user_id, session_id, requested_format=None):
    payload = {
        "conversation": conversation,
        "user_id": user_id,
        "session_id": session_id,
        "publisher_key": PUBLISHER_KEY,
        "requested_format": requested_format,  # optional
    }
    r = requests.post(f"{BASE_URL}/v1/analyse", json=payload)
    return r.json()

# Response handling — check format, render accordingly
def render_ad(response):
    if not response["ad"]:
        return  # no ad for this turn

    fmt = response["format"]
    serve = response["ad"]["serve"]

    if fmt == "teaser_hook":
        show_question(serve["teaser_question"], serve["quick_replies"])
    elif fmt == "inline_text":
        show_banner(serve["text"], serve["cta_url"])
    elif fmt == "text_voice_card":
        show_card(serve["card"])
    elif fmt == "mcp_transaction_card":
        show_buy_card(serve["card"], response["ad"]["action"])
    elif fmt == "post_conv_chip":
        show_chip(serve["sponsored_chip"])
    elif fmt == "predictive_push":
        send_push(serve["title"], serve["body"], serve["cta_url"])
    elif fmt == "mcp_tool_chip":
        show_tool_chip(serve["chip_label"], response["ad"]["action"])
```

---

## What NOT to touch

- `admind-tester.html` — separate demo tool, already deployed, attached to another website. Leave as-is.
- `campaigns/sample_*.json` — inactive reference files. `active: false`.
- `.env` — never commit, contains real API keys.
