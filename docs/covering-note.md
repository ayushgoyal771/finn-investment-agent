# Founding AI Engineer covering note

This is the public covering-note draft for **Ayush Goyal**. No assessment email has been sent. The private email copy includes contact details and a reminder to insert the workspace token; credentials are not published here.

**To:** assessment@enam.com

**Subject:** IIT Delhi – Founding AI Engineer - 2027

---

Hi ENAM Team,

My name is Ayush Goyal. Please find my submission for the Founding AI Engineer Build Challenge.

- Live prototype: https://finn-investment-agent-ayush.onrender.com
- GitHub repository: https://github.com/ayushgoyal771/finn-investment-agent
- AI build history: Attached as Ayush_Goyal_FINN_Build_Record.md. It is also available in the repository under docs/ai-build-history.
- Demo access: protected by a workspace token, to be supplied privately to the reviewers.

I built FINN, a mobile-first investment research prototype with three connected workflows: portfolio signals, company research and professional network context.

The Push workflow brings together announcements for an 18-company mock portfolio and end-of-day price and volume alerts. Users can choose the time window, change thresholds and save important signals. A clearly labelled fictional CFO example shows the person's career and a second-degree connection through the investor's network.

The Pull workflow uses annual reports and earnings-call transcripts, with source links and page references. It includes historical FY2025 evidence packs for TCS, Infosys and Asian Paints, plus live document discovery for other NSE tickers where documents are available. It shows missing evidence and source errors. Screener is used to find document links, not as research evidence.

The Network workflow includes eight synthetic profiles with career history, expertise search, relationship paths and reconnect prompts. Relevant people also appear within signals and research.

I used Python and FastAPI with SQLite and a responsive HTML, CSS and JavaScript interface. One Render service runs the frontend and backend. Separate modules handle sources, research, signals, storage and network matching. Caching and bounded document processing keep the prototype small and inexpensive.

Rules handle calculations and ranking. Optional OpenAI synthesis is implemented using retrieved public evidence and citation checks. No model key is configured on the deployment, and I have not verified a credentialed model call. There are no autonomous agents or trading actions.

All profiles and relationships are synthetic. The hosted app uses a workspace access token, and private network profiles are excluded from model input. This is a single shared workspace; production use would need individual accounts, tenant isolation, encrypted storage and consent controls.

The recorded checks passed 84 tests: 74 Python tests and 10 DOM integration tests. Hosted checks also covered desktop and phone-sized browser views. During verification, NSE filings and transcript research worked, but Yahoo prices were rate-limited from Render and a large annual report timed out. Free hosting may take time to wake up and can reset saved data.

I left out real-contact import, OCR, intraday data, mobile notification delivery and complete financial-table extraction. The quarterly-results comparison is a labelled synthetic example; a complete four-quarter guidance-versus-delivery tracker is not implemented. My next steps would be more reliable data feeds, stronger extraction checks, a quarterly fact store, a guidance tracker and persistent storage.

I used ChatGPT/Codex for development, troubleshooting and deployment. The attachment contains selected actual messages and a factual build summary. Suggested prompts for future work are clearly marked separately; they are not presented as earlier conversation.

Thank you for reviewing my submission. I would be happy to explain the implementation and design choices.

Best regards,
Ayush Goyal
