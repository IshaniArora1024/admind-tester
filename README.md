# AdMind API

## What This Is

AdMind API is the brain of the AdMind SDK. It receives conversation history from a publisher's app, detects the user's intent using the Gemini AI model (with keyword matching as a fallback), and returns the right ad payload from the right advertiser campaign — all in real time. Publishers integrate the SDK into their chat apps; this API does all the heavy lifting invisibly in the background.

## How It Works (plain English, no jargon)

```
Publisher app  →  POST /v1/analyse  →  Intent detection  →  Campaign match  →  Ad payload
     │                                      │                      │                │
     │                                 Gemini API            vip_luggage.json    teaser_hook /
  Sends last                          (or keywords                               inline_text /
  10 messages                          as fallback)                              post_conv_chip
```

1. Your app sends the last 10 chat messages to `/v1/analyse`.
2. AdMind figures out what the user is thinking (e.g. they need luggage for a trip).
3. It finds the best matching ad campaign and the right format to show.
4. It returns a ready-to-render ad payload — or `null` if nothing fits.

---

## Prerequisites

- Python 3.10 or higher
- A Gemini API key (free at [aistudio.google.com](https://aistudio.google.com))

---

## Setup — Step by Step

### Step 1 — Download Python

If you don't have Python, go to [python.org/downloads](https://python.org/downloads) and install Python 3.10+.

To check if you have it: open terminal and type:
```
python --version
```

### Step 2 — Open Terminal in the project folder

**On Windows:** Open the `admind-api` folder, click the address bar at the top, type `cmd`, press Enter.

**On Mac:** Right-click the `admind-api` folder, select "Open Terminal Here".

### Step 3 — Create a virtual environment

This keeps the project's dependencies separate from your system.

```
python -m venv venv
```

### Step 4 — Activate the virtual environment

**Windows:**
```
venv\Scripts\activate
```

**Mac/Linux:**
```
source venv/bin/activate
```

You'll see `(venv)` appear in your terminal. That means it worked.

### Step 5 — Install dependencies

```
pip install -r requirements.txt
```

Wait for it to finish. This installs FastAPI and all other packages.

### Step 6 — Set up your environment variables

Copy `.env.example` to a new file called `.env`:

**Windows:**
```
copy .env.example .env
```

**Mac/Linux:**
```
cp .env.example .env
```

Open `.env` and fill in:
```
GEMINI_API_KEY=your_key_from_aistudio.google.com
ADMIND_MASTER_KEY=admind_test_key_123
```

Keep `ADMIND_MASTER_KEY=admind_test_key_123` as-is for testing.

### Step 7 — Run the API

```
uvicorn main:app --reload
```

You should see:
```
AdMind API started. Docs at http://localhost:8000/docs
[AdMind] Loaded 1 active campaign(s).
```

### Step 8 — Test it in your browser

Open: [http://localhost:8000/docs](http://localhost:8000/docs)

You will see the interactive API docs. Click any endpoint to test it live.

---

## Testing the API

### Test 1 — Root check

Open browser: [http://localhost:8000](http://localhost:8000)

Expected response:
```json
{"name": "AdMind API", "status": "running", ...}
```

### Test 2 — Analyse a conversation (luggage intent)

In the `/docs` page, click `POST /v1/analyse` → `Try it out` → paste this body:

```json
{
  "conversation": [
    {"role": "user", "content": "I just booked flights to Goa for 5 people"},
    {"role": "assistant", "content": "Great! Goa in May is lovely."},
    {"role": "user", "content": "I need to sort out luggage for everyone"}
  ],
  "user_id": "test_user_001",
  "publisher_key": "admind_test_key_123"
}
```

**Expected:** Returns a `teaser_hook` or `inline_text` payload for VIP Luggage.

### Test 3 — Analyse a conversation (flight booked)

```json
{
  "conversation": [
    {"role": "user", "content": "Book me flights to Kerala for 3 people"},
    {"role": "assistant", "content": "Done! Your flights are confirmed."},
    {"role": "user", "content": "Perfect, thank you"}
  ],
  "user_id": "test_user_002",
  "publisher_key": "admind_test_key_123",
  "trip_confirmed": true
}
```

**Expected:** Returns `text_voice_card` or `teaser_hook` payload.

### Test 4 — Conversation ended (chips)

```json
{
  "conversation": [
    {"role": "user", "content": "That's everything, thank you so much!"},
    {"role": "assistant", "content": "Have a great trip!"}
  ],
  "user_id": "test_user_003",
  "publisher_key": "admind_test_key_123",
  "conversation_ended": true
}
```

**Expected:** Returns `post_conv_chip` payload.

### Test 5 — Predictive push

```json
{
  "conversation": [
    {"role": "user", "content": "My flight is in 6 days"}
  ],
  "user_id": "test_user_004",
  "publisher_key": "admind_test_key_123",
  "days_before_departure": 6
}
```

**Expected:** Returns `predictive_push` payload.

### Test 6 — Invalid key

```json
{
  "conversation": [{"role": "user", "content": "Hello"}],
  "user_id": "test_user_005",
  "publisher_key": "wrong_key"
}
```

**Expected:** `401` error with code `ADMIND_001`.

### Test 7 — No match (returns null)

```json
{
  "conversation": [
    {"role": "user", "content": "What is the weather like today?"}
  ],
  "user_id": "test_user_006",
  "publisher_key": "admind_test_key_123"
}
```

**Expected:** `{"ad": null, "format": null, "triggered_by": null}`

---

## Logs

After running tests, check:

```
logs/impressions.jsonl   — every ad shown to a user
logs/clicks.jsonl        — every CTA tapped by a user
```

Each line is one JSON event. Example:
```json
{"ad_id": "vip_001_teaser_hook_20240101120000", "user_id": "test_user_001", "format": "teaser_hook", "publisher_key": "admind_test_key_123", "timestamp": "2024-01-01T12:00:00+00:00"}
```

---

## Adding a New Advertiser Campaign

1. Create a new JSON file in the `campaigns/` folder.
2. Follow the structure of `vip_luggage.json` exactly.
3. Set `"active": true`.
4. Restart the server — it will auto-load the new campaign.

No code changes needed. The campaign loader refreshes every 60 seconds during runtime.

---

## Deploying to Firebase (later)

Instructions coming in Step 2 of the AdMind build.
