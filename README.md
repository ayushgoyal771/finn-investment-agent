# FINN · An investor’s quiet advantage

A responsive investment research prototype for the ENAM Founding AI Engineer build challenge. FINN connects **what changed**, **what the primary evidence says**, and **who in your network can add context**.

The application is one Python service with a buildless HTML/CSS/JavaScript frontend. No frontend build, account, API key, or paid service is needed for the complete demonstration.

## Run locally

Python 3.12+ is required. From this repository, on Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\python -m pip install -r requirements.txt -c backend/requirements.lock
.\.venv\Scripts\python run.py
```

On macOS/Linux:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt -c backend/requirements.lock
.venv/bin/python run.py
```

Open [FINN locally](http://127.0.0.1:8000). If port 8000 is occupied, use `python run.py --port 8001` with your environment’s Python executable. Stop with Ctrl+C.

The delivered workspace already has the Python environment installed. Start it with `.\.venv\Scripts\python run.py`.

## A three-minute demonstration

1. **Today’s brief:** open the PI Industries leadership signal. Follow **You → Meera Shah → Rohan Desai**. Read the incoming executive’s career and the explicit relationship evidence. This entire event and every person are fictional, prominently labelled in the interface.
2. Open the Asian Paints scenario. Compare Revenue, EBITDA, PBT and PAT with the prior quarter and prior year. The figures in this particular scenario are synthetic; historical research evidence is separate.
3. Save a signal, open Saved, then adjust Alert preferences. Raise price and volume thresholds to remove triggered market signals. Corporate filings remain in the digest even when announcement alerts are disabled. Change the digest from 24 hours to 7 days to see older events.
4. **Research:** choose Asian Paints and ask about volume versus value, TCS for growth and margins, or Infosys for cash conversion. Each historical pack cites the original FY2025 annual report and transcript. Evidence can be downloaded as a Markdown brief.
5. **Your network:** search semiconductors, specialty chemicals, IT services, rural lending, a person’s name or a ticker. Open the relevant career history and use “Spoke today” to update the last-contact date.
6. **Beyond the demo:** choose Live discovery in Research and enter **HCLTECH**, or another NSE ticker. FINN discovers primary document links, reads available PDFs, retrieves relevant passages and attaches page-level citations. This path is independent of the bundled company packs.

## What works

| Layer | Implemented workflow |
|---|---|
| Push | 18-company mock portfolio; 24h/48h/7d digest; deterministic category ranking; collapsed routine filings; configurable material-event and EOD price/volume alerts; saved/read state |
| Pull | Three attributed historical research packs; live document discovery for arbitrary NSE symbols; PDF text extraction and passage retrieval; source links, coverage and gaps; optional model synthesis; evidence export |
| Network | Eight synthetic profiles; employer/peer/theme relevance; career tenure; explicitly attested second-degree path; possible-overlap labelling; reconnect prompts; conversation dates and export |

Network context appears inside both signal details and research. Career overlap alone never becomes a claim that two people know each other.

## Data modes and sources

**Demo workspace** uses fictional events, prices, volumes and profiles. The scenario timeline is relative to server startup and is labelled accordingly. Research packs contain a small, manually checked set of historical facts from issuer annual reports and transcripts for the year ended March 2025. They are not current financial assessments or comprehensive report summaries.

**Live sources** fetch daily Yahoo Finance bars for the portfolio and NSE’s public announcements endpoint. The most recent session is excluded until 15:35 IST on the current day. The volume baseline is the *prior* 20 completed sessions, excluding the observed session. Prices are raw provider daily closes; corporate actions can affect percentage changes and should be checked. A holiday/weekend does not create a new trading observation.

**Live discovery** uses Screener only as a directory of annual-report and transcript links. Screener commentary and financial tables never enter research. For an unknown ticker, only exchange-filed originals are accepted. A few verified issuer URLs provide fallbacks for the three historical demonstration companies. HTTP denial, missing PDFs, unreadable documents and insufficient evidence stay visible; live mode never falls back to fictional facts.

In-app live refresh runs every five minutes while the page is visible. Server background refresh is optional. This is a polling prototype, not an intraday terminal or a mobile notification service. Source access and endpoint stability can change; observe provider terms and use licensed feeds for a production service.

## Optional model synthesis

Copy `.env.example` to `.env`, set `OPENAI_API_KEY` on the server, and restart. The research checkbox then enables an optional Responses API call using `gpt-4.1-mini` by default (`FINN_MODEL` overrides it). Only retrieved public financial evidence and the question are sent. Contact profiles and the private relationship graph are not included in this payload. Do not put private contact information into the research question.

The response uses a strict schema. Each claim requires valid retrieved source identifiers; malformed, incomplete or uncited output is rejected. This validates provenance identifiers, **not factual entailment**. The UI explicitly labels model interpretation for review. There are no autonomous agents, trading tools or model calls during feed refresh. Without a key, FINN provides evidence retrieval and curated historical briefs rather than pretending to run a model.

## Private access and phone use

Default binding is loopback. For another device on your trusted local network, configure `.env`:

```dotenv
FINN_ACCESS_TOKEN=replace-with-a-long-random-secret
FINN_ALLOWED_HOSTS=localhost,127.0.0.1,[::1],192.168.1.20
```

Use your computer’s actual LAN IP in place of `192.168.1.20`. Then run `python run.py --host 0.0.0.0` and open `http://YOUR_LAN_IP:8000` on the phone. Enter the configured access token. Token protection and an allowed host are mandatory for non-local access. For hosting or untrusted networks, use an HTTPS reverse proxy; do not expose plain HTTP publicly. Do not open firewall access beyond what you intend.

This prototype is single-user. All users with the same server token share one workspace. It has no tenant isolation, encrypted database, real contact import, SSO or production audit trail. See [architecture and privacy](docs/architecture.md) before adapting it to real personal data.

## Verification

Install the test dependencies, then run:

```powershell
.\.venv\Scripts\python -m pip install -r requirements-dev.txt -c backend/requirements.lock
.\.venv\Scripts\python scripts/check.py
```

Optional interface integration tests require Node.js 24+:

```powershell
npm ci
npm test
```

The DOM tests load the actual interface with in-process API fixtures and mocked fetch. They make **no browser or network requests** and do not verify rendering, layout or contrast. Browser preview permission was declined during this build, so actual desktop/phone visual QA remains unverified. See [validation results](docs/validation.md).

Live checks are opt-in and make outbound public-source requests:

```powershell
.\.venv\Scripts\python scripts/live_probe.py
.\.venv\Scripts\python scripts/research_probe.py
```

They write availability summaries under ignored `artifacts/`. They do not require or invoke a model. The first checks all data-source types; the second exercises full research for HCLTECH, which is not a bundled demo company.

## Containers

For the prepared **free Render deployment**, see [deployment instructions](docs/deployment.md) and the root `render.yaml`. This option uses ephemeral SQLite storage and does not provision paid resources.

```bash
docker build -t finn .
docker run --rm -p 8000:8000 --env-file .env -v finn-data:/app/data finn
```

Set `FINN_ACCESS_TOKEN` first. Add your hostname to `FINN_ALLOWED_HOSTS`. Run one service worker with a persistent `/app/data` volume. Container configuration is provided; Docker execution was not available/verified in this build.

## Repository guide

```text
backend/
  main.py          HTTP API, access controls, lifecycle
  service.py       Portfolio digest and alert assembly
  providers.py     Market, exchange, discovery and PDF adapters
  research.py      Evidence retrieval and optional cited synthesis
  network.py       Explainable experience and relationship matching
  evidence.py      Attributed historical evidence packs
  seed.py          Explicitly fictional demo data
  db.py            SQLite state and bounded TTL caches
frontend/          Responsive UI, no runtime package dependencies
scripts/           Check runner and opt-in source probes
tests/             Finance, network, API, source and DOM integration tests
docs/              Architecture, scope map, covering note and build summary
```

## Deliberate limits

Live research provides cited excerpts and optional model interpretation. It does not reliably normalize arbitrary PDF financial tables, build a four-quarter promise-versus-delivery ledger, or calculate every ratio in the reference glossary. The comparative-results demo uses synthetic data, rather than mislabelling a hand-entered table as extracted. Network data is synthetic and there is no LinkedIn scraping. Scanned PDFs need OCR, which is not implemented.

The repository, deployment and assessment email have not been published/sent. The PDFs describe submission expectations; the user requested creation of the local codebase. A [covering-note draft](docs/covering-note.md), [requirements map](docs/requirements.md), and [honest build summary](docs/build-history.md) are included for the handoff.
