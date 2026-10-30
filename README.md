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

## Ask Dalil (chat about a scanned document)

Under every result there is a chat. People can ask follow-up questions in their language: where to pay, instalments, what happens if they pay late, which documents to bring.

- **Grounded first:** answers use the document's details and the matched record from `data/services.json` (looked up on the server).
- **Live, but only official:** with `AI_PROVIDER=claude` the AI can search the web in real time, limited to official UAE government websites (`OFFICIAL_SITES` in `app/chat.py`: u.ae, rta.ae, dubaipolice.gov.ae, icp.gov.ae, gdrfad.gov.ae, dubailand.gov.ae, tamm.abudhabi...). Each answer shows the official pages it used as links. Non-official links are dropped.
- **Private:** only the type, authority, emirate, subject, amount and dates are sent, never the photo, names, or reference, plate or ID numbers.
- **Safe:** no legal advice, it never asks for card numbers, passwords or OTPs, and it only points to official payment channels.
- With Gemini, or if web search is switched off for the API account, it still answers from the checked data and says live search is off. Web search costs about $10 per 1,000 searches on top of normal Claude usage (max 3 searches per question).

## Accounts (optional)

People can use Dalil without an account: saved documents then stay in that browser only. With an account (email and password), saved documents sync across every device where they sign in.

- **Privacy is enforced on the server.** `app/accounts.py` keeps only an allow-list of fields: type, authority, emirate, subject, amount, dates, summary, official link and status. Everything else is dropped, including names, reference or plate numbers, ID numbers and photos.
- **Passwords** are stored as salted scrypt hashes.
- **"Delete my account and data"** removes everything.
- Data is stored in `data/dalil.db` (SQLite), which git ignores.
- Set `SECRET_KEY` in `.env` so people stay signed in when the app restarts.
- Another device on the same Wi-Fi uses the same server, so it sees the same account.

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
| `app/main.py` | Web server and API: `/analyze`, `/chat`, `/services`, `/languages`, `/health` | everyone |
| `app/chat.py` | Ask Dalil: follow-up chat with live search on official sites only (AI) | AI |
| `web/index.html` | App page: header, tab bar, one `<section>` per tab | UI |
| `web/css/app.css` | All styles. Colours and sizes are variables at the top | UI |
| `web/js/app.js` | Switches tabs (`#scan`, `#deadlines`, `#services`, `#how`) | UI |
| `web/js/i18n.js` | Every interface text, ready for translation (#16) | UI |
| `web/js/scan.js` | Scan tab: upload, progress steps, result (#12) | UI |
| `web/js/chat.js` | Ask Dalil chat card under the result (#19) | UI |
| `web/js/deadlines.js` | My documents tab: saved documents, deadlines, paid status, Add to calendar | UI |
| `web/js/account.js` | Sign in, create account, sign out, delete account | UI |
| `web/js/store.js`, `web/js/calendar.js` | Saving documents (this phone, or the account when signed in); building the calendar file | UI |
| `web/js/services.js` | Services tab: the verified catalog, filters, open data used (#14) | UI |
| `web/js/how.js` | How it works tab, placeholder for #15 | UI |
| `app/pipeline.py` | Connects all the steps | everyone |
| `app/accounts.py` | Accounts and synced documents (privacy allow-list) | everyone |
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
