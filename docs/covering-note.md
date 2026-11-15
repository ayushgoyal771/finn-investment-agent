# Founding AI Engineer covering note

Public covering-note draft for **Ayush Goyal**. No assessment email has been sent. The private email copy includes contact details; the public demo requires no credentials.

**To:** assessment@enam.com

**Subject:** IIT Delhi – Founding AI Engineer - 2027

---

Hi ENAM Team,

My name is Ayush Goyal. Please find my submission for the Founding AI Engineer Build Challenge.

- Live prototype: https://finn-investment-agent-ayush.onrender.com
- Public repository: https://github.com/ayushgoyal771/finn-investment-agent
- AI build history: https://github.com/ayushgoyal771/finn-investment-agent/blob/main/docs/ai-build-history/Ayush_Goyal_FINN_Build_Record.md
- Attached note: Ayush_Goyal_FINN_Development_Retrospective.md

The prototype opens directly in the browser without a login or access token.

I built FINN, a mobile-first investment research prototype with three connected workflows: portfolio signals, company research and network context.

The Push workflow covers an 18-company mock portfolio. It brings together announcements and end-of-day price and volume signals, with configurable thresholds, time windows and saved items. A clearly labelled fictional CFO example connects the announcement to the person's career and a second-degree relationship path.

The Pull workflow uses annual reports and earnings-call transcripts, keeping source links and page references visible. It includes historical FY2025 evidence packs for TCS, Infosys and Asian Paints, plus live discovery for other NSE tickers where primary documents are available. Missing evidence and source failures are shown clearly.

The Network workflow includes eight synthetic profiles with career details, expertise search, relationship paths and reconnect prompts. Relevant people also appear inside signals and research.

I used Python, FastAPI, SQLite and a responsive HTML, CSS and JavaScript frontend. One free Render service hosts the app. Separate modules handle sources, signals, research, network matching and storage. Caching and bounded document processing keep the prototype small.

Calculations and ranking use deterministic rules. Optional synthesis is implemented with gpt-4.1-mini using retrieved public evidence and citation checks. Model calls are disabled in the public demo, and no credentialed model call has been verified. There are no autonomous agents or trading actions.

All profiles and relationships are synthetic. The public demo shares saved items and preferences between visitors. Real use would need individual accounts, tenant isolation, encrypted storage and consent controls.

The implementation passed 89 tests: 78 Python tests and 11 DOM integration tests. Desktop and phone-sized browser views were checked. A fresh recheck confirmed that signals, historical research and network access work without a token. During earlier live-source checks, NSE filings and transcript research worked, while Yahoo prices were rate-limited from Render and a large annual report timed out. Free hosting can sleep and reset saved data.

I left out real-contact import, OCR, intraday data, mobile notification delivery and complete financial-table extraction. The quarterly-results comparison is a labelled synthetic example; a complete four-quarter guidance-versus-delivery tracker is not implemented. My next steps would be more reliable feeds, stronger extraction checks, a quarterly fact store, a guidance tracker and persistent storage.

I used ChatGPT/Codex for development, troubleshooting and deployment. The linked build history contains selected actual messages, with its scope stated. The attached retrospective explains the decisions and corrections and includes clearly labelled rewritten prompt examples. Those examples are separate from the original conversation.

Thank you for reviewing my submission. I would be happy to discuss the implementation and design choices.

Best regards,
Ayush Goyal
