# Covering-note draft

Subject requested by the challenge: `IIT Delhi – Founding AI Engineer - 2027`

This is a draft for the owner to review and send. No email has been sent. The source repository and free Render demo below have been published.

---

Hello ENAM team,

I built FINN as an investor’s fieldnotes: a quieter, connected workflow from an important portfolio event to primary evidence and the person best placed to add context.

The prototype watches an 18-company mock portfolio, ranks disclosures, collapses routine paperwork, and lets the investor choose material-announcement and EOD price/volume thresholds. Network context is embedded in signal details and research. A fictional CFO appointment demonstrates an explicitly attested second-degree introduction; a results scenario demonstrates Revenue, EBITDA, PBT and PAT comparisons. These examples are labelled synthetic throughout.

Research uses company annual reports and transcripts. Three compact FY2025 packs make the demonstration work immediately; live discovery works independently for arbitrary NSE tickers where primary PDFs are available. I exercised HCLTECH outside the demonstration set. Source access failures and evidence gaps are visible. Screener is only a link directory; broker notes, news and its commentary never become research evidence.

I chose a single Python service, SQLite, and a responsive buildless frontend to keep setup and operating cost low. Deterministic rules handle routing, ranking, numerical comparisons and network matching. Optional small-model synthesis is requested explicitly, receives retrieved public evidence, requires cited claim IDs and keeps the private graph out of the payload. It is labelled an interpretation for review; citation validity is not represented as proof of factual correctness.

All network profiles are invented. The local prototype uses loopback by default and token protection for remote access. The architecture note covers provenance, refresh/cache policies, consent, retention, tenant isolation and the cloud design I would use before handling a real investor’s network.

I deliberately left out intraday prices, mobile notification delivery, real-profile ingestion, OCR and comprehensive arbitrary-table normalization. The comparative-results example is a demonstration rather than a claim of automated filing extraction. I would next build a reconciled quarterly fact store and a reviewable management-guidance ledger, then add licensed feeds, authenticated multi-tenant storage and extraction evaluation.

Automated checks and source probes are recorded in the validation note. The deployed app was checked in desktop and phone-sized browser viewports. On the free cloud instance, NSE filings and live transcript research work; Yahoo daily-bar requests currently return HTTP 429, and a large annual report timed out. The historical demonstration works without these external requests. Free hosting can sleep and reset saved state.

Prototype: https://finn-investment-agent-ayush.onrender.com

Public repository: https://github.com/ayushgoyal771/finn-investment-agent

AI session history: [attach authentic coding-session export or owner-created share link]

Regards,

[Your name]
