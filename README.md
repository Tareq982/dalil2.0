# Dalil · دليل

Dalil is an AI guidance agent that helps residents who can't easily read Arabic or English understand official documents. Send it a photo of a fine, visa notice or lease, and it explains, in your language, what the document means, what it costs, the deadline and the exact next step, with a link to the official service.

Hackathon 2026 · Theme: **Zero Bureaucracy & Seamless Government** (secondary: Inclusive Digital Accessibility)

## How it works

```
photo ──► extract.py ──► catalog.py ──► explain.py ──► safety.py ──► reply
          (AI reads)     (code matches   (AI explains    (code adds confidence,
                          verified data)  only those      source, official link,
                                          facts)          not-legal-advice)
```

- **Grounded:** fees, deadline rules and links come from `data/services.json`, built from open data and official pages, never from the AI's memory.
- **Responsible AI:** shows its confidence, refuses to guess below `MIN_CONFIDENCE`, always links the official source, and gives no legal advice.
- **No storage:** photos stay in memory for one request.

## Quick start

**Windows (cmd):**
```
cd dalil2.0
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
```

**Mac / Linux / Codespaces:**
```
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Then open `.env` (`notepad .env` on Windows) and add an AI key:

- **Gemini (free tier):** get a key at [aistudio.google.com](https://aistudio.google.com), set `AI_PROVIDER=gemini` and paste it after `GEMINI_API_KEY=`. The free tier may use what you send to improve Google's products, so **test with mock documents only**.
- **Claude:** get a key at [platform.claude.com](https://platform.claude.com/settings/keys), set `AI_PROVIDER=claude` and paste it after `ANTHROPIC_API_KEY=`.

Then run:

```
python -m app.main
```

Open **http://localhost:8000**, upload a document photo, and pick a language.

> **No API key yet?** Leave it empty. The app runs in **mock mode** and returns a fake answer, so you can still work on the app's look and on the data.

**Run the tests** (no API key needed):
```
python -m pytest
```

## Project layout

| Path | What | Owner |
|---|---|---|
| `app/extract.py` | Reads the photo and returns structured fields (AI) | AI |
| `app/explain.py` | Writes the explanation in the user's language (AI) | AI |
| `app/safety.py` | Confidence, fallback, disclaimer text in every language (code) | AI |
| `app/catalog.py` | Matches fields to a verified service record (code) | Data |
| `data/services.json` | The verified service catalog | Data |
| `data/sources.md` | Where every value came from, plus the open datasets used | Data |
| `tools/lookup_service_prices.py` | Looks up official fees in the Dubai Government Service Prices open dataset | Data |
| `app/main.py` | Web server and API: `/analyze`, `/services`, `/languages`, `/health` | everyone |
| `web/index.html` | App page: header, tab bar, one `<section>` per tab | UI |
| `web/css/app.css` | All styles. Colours and sizes are variables at the top | UI |
| `web/js/app.js` | Switches tabs (`#scan`, `#deadlines`, `#services`, `#how`) | UI |
| `web/js/i18n.js` | Every interface text, ready for translation (#16) | UI |
| `web/js/scan.js` | Scan tab: upload, progress steps, result (#12) | UI |
| `web/js/deadlines.js` | My deadlines tab: saved deadlines, days left, Add to calendar (#13) | UI |
| `web/js/store.js`, `web/js/calendar.js` | Saving deadlines on the phone only; building the calendar file | UI |
| `web/js/services.js` | Services tab: the verified catalog, filters, open data used (#14) | UI |
| `web/js/how.js` | How it works tab, placeholder for #15 | UI |
| `app/pipeline.py` | Connects all the steps | everyone |
| `app/ai.py` | Talks to Gemini or Claude (chosen by `AI_PROVIDER` in `.env`) | AI |
| `samples/` | Mock documents and expected answers | Demo |
| `tests/` | Automated checks, run with `python -m pytest` | everyone |

## Extracted fields (team contract)

`extract.py` always returns exactly these keys. Change them only in a pull request that also updates `catalog.py`, `explain.py` and this table.

| Key | Type | Example |
|---|---|---|
| `doc_type` | `traffic_fine` / `visa_residency_notice` / `tenancy_contract` / `other` | `traffic_fine` |
| `emirate` | string or null | `Dubai` |
| `issuing_authority` | string or null | `Dubai Police` |
| `reference_number` | string or null | `12345678` |
| `amount_aed` | number or null | `600` |
| `issue_date` | `YYYY-MM-DD` or null | `2026-10-20` |
| `deadline_date` | `YYYY-MM-DD` or null (only if printed) | `null` |
| `subject` | string or null, in English | `Exceeding the speed limit` |
| `key_points` | list of up to 5 strings | |
| `keywords` | list of up to 8 lowercase words, used for matching | `["speed","radar"]` |
| `document_language` | `ar` / `en` / `mixed` / `other` | `mixed` |
| `readable` | bool | `true` |
| `confidence` | 0–1 | `0.9` |

Personal data (names, Emirates ID, passport and phone numbers) is deliberately **not** extracted.

## Team rules

- Never push straight to `main`. Make a branch, open a pull request, and have one teammate review it.
- Never commit `.env` or API keys.
- Never commit real people's documents. Use mock samples only (see `samples/README.md`).
- Every value in `services.json` needs a source in `data/sources.md`. Set `"verified": true` only once it's checked. The app shows a ⚠️ warning for unverified records.
