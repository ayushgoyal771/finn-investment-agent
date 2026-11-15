# Founding AI Engineer: requirements and scope

This implementation follows **FINN: Financial Investment Agent — Founding AI Engineer Build Challenge**. All three layers are present: Push, Pull and Network. This is the Founding submission; the separate AI Engineer submission described in a friend's email is not the source specification for this repository.

Submission subject: **IIT Delhi – Founding AI Engineer - 2027**.

The two PDFs are project reference material. Their submission email, public-repository request and deadline are not interpreted as permission to publish, send messages or change external accounts.

| Brief requirement / example | Implementation and evidence | Boundary |
|---|---|---|
| Mobile-first prototype | Responsive fieldnotes interface; mobile bottom navigation; source-labelled signal/detail/research/network flows | Desktop and 390px browser viewport verified after deployment; physical phone not tested |
| Portfolio of 15–20 companies | 18 NSE-listed symbols; sector and size labels in `backend/seed.py` | Mock watchlist; no real holdings |
| Three to five research demonstrations | TCS, INFY and ASIANPAINT historical evidence packs | Historical FY2025, not current coverage |
| Generalise to unseen NSE ticker | Live Screener document discovery → exchange PDFs → page-preserving extraction → retrieval; live HCLTECH check | Depends on source access and readable PDFs |
| Price and volume | Yahoo daily bars; completed-session gate; prior-20-session volume baseline | EOD only; raw closes can reflect corporate actions |
| Corporate filings | NSE public JSON feed; canonical IDs; date parsing; durable deduplication; category ranking | Public endpoint can change or deny access |
| Annual reports and transcripts | Discovery directory restricted to primary links; issuer fallback for known demo companies; PDF provenance and pages | No OCR; extraction limits; not every financial table is normalized |
| Profiles and network | Eight realistic synthetic profiles with roles, employers, tenure, education and expertise | No real profiles or LinkedIn scraping |
| Push workflow | Windowed digest, collapsed routine filings, configurable thresholds and category alerts | In-app polling; no OS push delivery |
| Leadership example | Fictional incoming CFO career plus attested second-degree path | Clearly a synthetic scenario; no claim of a real appointment |
| Results example | Four-metric comparative scenario, current/prior/year-ago quarter and QoQ/YoY | Synthetic demonstration; not advertised as real extraction |
| Primary-only Pull workflow | Cited annual report/transcript packs and live evidence retrieval; optional cited synthesis | No secondary news, broker notes or model company knowledge |
| Network woven into Push/Pull | Ranked people and suggested diligence questions in signal details and research | Relevance is contextual, not proof of private knowledge |
| Direct network workflow | Expertise/company/person search, career notes, reconnect prompts, conversation dates and export | Synthetic network; no real-contact CRUD |
| Architecture/security/cost writeup | `docs/architecture.md`; local loopback default; opt-in model in private mode; explicit public synthetic demo; TTL caches | Single user, no production tenancy or encryption |
| Repository and covering note | Public GitHub repository, free Render deployment, README, CI, Dockerfile, notes and tests | Assessment email not sent; free hosting has no durable SQLite storage |
| AI build history | `docs/ai-build-history/Ayush_Goyal_FINN_Build_Record.md` contains selected actual user/assistant messages and a factual retrospective | Export scope and redactions are stated; suggested future prompts are clearly separate from historical messages |

The brief treats the eight research outputs and detailed Push examples as a menu. This implementation prioritises the connected evidence/network workflow and clearly identifies the illustrative results-table limit. A production-grade four-quarter promise-versus-delivery ledger is deliberately not claimed.
