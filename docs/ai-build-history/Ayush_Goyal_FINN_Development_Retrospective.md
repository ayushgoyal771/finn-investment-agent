# Ayush Goyal - FINN development retrospective and prompt guide

**Challenge:** ENAM Founding AI Engineer

**Prepared:** 16 November 2026

**Author:** Ayush Goyal

- Live application: https://finn-investment-agent-ayush.onrender.com
- Public repository: https://github.com/ayushgoyal771/finn-investment-agent
- Selected actual conversation: https://github.com/ayushgoyal771/finn-investment-agent/blob/main/docs/ai-build-history/Ayush_Goyal_FINN_Build_Record.md

## About this document

This document was prepared after development. It explains the implemented product, engineering decisions, corrections and verification. The prompt examples are rewritten retrospective examples of how to specify the work clearly. They are **not a verbatim chat export, not claims about prompts previously used, and not evidence that proposed future work has been completed**.

The selected actual conversation is available at the link above, with its export scope and redactions stated. It remains the record of the original messages. This retrospective supplements that record.

The goal of the prompt guide is practical: make each request narrow enough to verify, name its data boundaries, and define observable acceptance criteria. A polished description alone is not evidence of a working implementation.

## 1. Product scope and what works

FINN connects three questions: what changed in a portfolio, what the primary evidence says, and who in an investor's network could add context.

| Layer | Working behavior | Important boundary |
|---|---|---|
| Push | An 18-company mock NSE portfolio, windowed filing digest, ranked categories, configurable end-of-day price/volume thresholds, read and saved state | Fictional events and market scenarios are labelled; cloud market-provider access can fail |
| Pull | Three historical FY2025 evidence packs, generic NSE document discovery, PDF passage retrieval, source links and page locators, evidence export | This is an excerpt-based research workflow, not comprehensive financial-table reconciliation |
| Network | Eight synthetic profiles, expertise/company/person search, career context, an attested second-degree path, reconnect prompts and contact dates | Career overlap indicates possible context; it does not prove a personal relationship |

Network context appears inside both signals and research. It is also directly searchable. The prototype follows the Founding AI Engineer brief, which asks for all three layers.

The quarterly-results scenario compares Revenue, EBITDA, PBT and PAT with the previous quarter and year-ago quarter. Those scenario figures are synthetic. A complete four-quarter guidance-versus-delivery tracker is not implemented.

The historical research packs contain attributed FY2025 company facts. Their historical period remains visible. They should not be read as a current assessment or as synthetic market news.

## 2. Architecture and trade-offs

The app uses Python and FastAPI with SQLite and a buildless HTML/CSS/JavaScript interface. A single Render service hosts the frontend and API.

This keeps the demonstration portable and avoids a separate frontend deployment, queue and vector database. It also creates limits: one shared workspace, ephemeral storage on the selected free tier, and no horizontal-scaling design.

Separate modules handle source fetching, signal assembly, research, network relevance, historical evidence, fictional fixtures and storage. Deterministic rules handle thresholds and ranking. Retrieval uses a token-overlap baseline with small topic expansions, which is easy to inspect but less capable than a carefully evaluated semantic retriever.

Optional model synthesis is implemented with gpt-4.1-mini, bounded retrieved public evidence and citation validation. It is disabled in the public demo. No credentialed model call was verified. There are no autonomous agents or trading tools.

All network profiles are synthetic. The public demo opens without a login and shares saved signals, preferences and contact dates between visitors. Private mode retains token protection. Real personal data would require individual accounts, tenant isolation, encrypted storage, consent and retention controls.

## 3. Retrospective prompt examples

**Every prompt in this section is a rewritten example prepared for this retrospective, not a historical message.** Each example includes a goal, constraints and a way to judge the result.

### Example 1: turn an ambiguous brief into a small deliverable

> Read the Founding AI Engineer brief and its financial reference. Build a requirement map before changing code. For Push, Pull and Network, select one complete user flow that can be demonstrated on a phone-sized screen. Map each flow to its data source, API behavior, interface and verification method. Keep required layers separate from illustrative examples. Mark synthetic scenarios, unsupported outputs and future production features explicitly. Use the smallest architecture that can run locally without paid services.

Why this is useful: it prevents a broad feature list from replacing a usable product. The requirement map should let a reviewer trace each claimed flow to implementation and evidence.

### Example 2: make architectural assumptions visible

> Propose one service that serves the API and responsive frontend, with SQLite for the demonstration. Explain how market observations, filing identifiers, PDF evidence, preferences and contact dates are stored. Separate public-source caches from workspace state. Define cache freshness, deduplication and saved-signal behavior. State what would need to change for multiple investors or multiple workers. Do not describe proposed tenant isolation, encryption or durable scheduling as implemented features.

Acceptance: the architecture note agrees with the code and deployment. A saved observation should not disappear simply because a later market session arrives or a threshold changes.

### Example 3: specify finance calculations precisely

> Review the end-of-day signal calculations. Price movement must use the intended completed observations. Volume must compare the observed session with the prior 20 completed sessions, excluding the observed session itself. Apply strict threshold semantics consistently. Handle missing, duplicated, nonfinite and zero-baseline data explicitly. Explain the effect of raw closing prices and corporate actions. Cover meaningful boundary cases rather than checking only the synthetic happy path.

Acceptance: the baseline does not include the observation being evaluated; undefined comparisons do not become invented growth percentages. Price and volume are attention signals, not forecasts.

### Example 4: make announcement ranking explainable

> Build a portfolio digest with 24-hour, 48-hour and seven-day windows. Retain filings in the digest even when their alert category is disabled. Rank material categories above routine paperwork, and collapse routine items without losing their source links. Show the reason a signal deserves attention and whether a relevant network person adds context. Treat source failure, an empty successful response and an outdated observation as different states.

Acceptance: changing an alert preference affects alerts as intended without silently deleting the filing record. Ranking remains deterministic and its reasons can be inspected.

### Example 5: distinguish a relationship from a possible overlap

> Use realistic synthetic profiles with roles, employers, tenure, education and expertise. For each company or topic match, explain why the person may help. Require overlapping dates before showing possible co-employment. A second-degree introduction must come from an explicit relationship attestation, not just a shared employer or university. Use stable person identifiers and label uncertain matches. Put useful network context inside a signal and a research result as well as in direct search.

Acceptance: a reviewer can distinguish an attested path from a possible overlap. The app never invents a friendship or implies access to a real person's private knowledge.

### Example 6: ground research in the right sources

> Accept an NSE ticker independently of the bundled demonstration companies. Use directory pages to discover annual-report and earnings-call document links, but admit only approved primary documents into the research evidence. Preserve original URLs, publication periods, page locators and content hashes. Report annual-report and transcript coverage separately. Exclude news, broker notes, directory financial tables and model memory as substitutes for missing primary evidence.

Acceptance: HCLTECH or another non-bundled ticker follows the live discovery path. A partial source set is reported as partial rather than presented as complete research.

### Example 7: define safe source-fetching behavior

> Review the source adapters for HTTPS, host restrictions, redirects, DNS checks, timeouts, byte limits, page limits and concurrent work. Revalidate redirects and reject unexpected content types. Keep normal certificate verification enabled. If a PDF cannot be read or a provider denies access, preserve a useful source-specific error. Explain any limitation of cancelling extraction work in a thread and identify where an isolated worker would be needed in production.

Acceptance: a provider error cannot silently become fictional data. A configured timeout is not described as proof that all underlying CPU or memory work has stopped.

### Example 8: constrain optional model synthesis

> Keep evidence retrieval useful without a model key. For explicitly requested synthesis in private mode, send only the question and bounded retrieved public excerpts. Exclude the network graph, credentials and private contact details from the payload. Treat document text as untrusted evidence. Require the response schema and cited identifiers to validate. Explain that a valid citation identifier does not prove factual support. Disable model calls completely in the public demo, including direct API requests.

Acceptance: missing keys do not cause pretend model output. Public mode cannot spend a configured model key. Unsupported claims require a separate evaluation process, not merely schema validation.

### Example 9: design a connected mobile workflow

> Organize the interface around a daily brief, research, network context and saved signals. Make the source, time window, evidence period and synthetic labels visible at the point of use. A leadership signal should lead to a career and relationship explanation. A research brief should lead back to original evidence and suggest a relevant conversation. Check navigation, dialog scrolling, loading and error states at a phone-sized viewport. Report the tested viewport rather than claiming a physical-device test.

Acceptance: a visitor can finish the three main flows without knowing the implementation. Loading a different data mode clears previous-mode prices and statistics before new results appear.

### Example 10: choose tests that expose real mistakes

> Verify calculations, date/session boundaries, relationship evidence, source restrictions, outages, saved-state behavior and API access controls with deterministic tests. Add interface integration checks for the actual HTML and JavaScript using API-generated fixtures. Include escaped external text and mode switching. Keep live source probes separate from deterministic tests. State clearly that DOM tests do not prove layout, contrast, screen-reader behavior or correctness on a physical phone.

Acceptance: tests fail for meaningful broken behavior. The validation record distinguishes test results, source-connectivity probes, hosted browser checks and unverified areas.

### Example 11: make the public deployment easy to review

> Deploy the existing app on the owner's approved $0 Render plan. Use the platform port and exact hostname, and keep secrets out of Git. Enable explicit public-demo mode so a new visitor can open the link without a token. Retain synthetic profiles and shared-state labels; block model calls in public mode. Confirm that CI passes and the intended source revision is deployed. Test the endpoints without an Authorization header and open a new browser tab before reporting success.

Acceptance: the health response identifies public mode with authentication off. Signals, research and network return usable responses without credentials. A deployment that has only started building is not reported as live.

### Example 12: audit submission claims

> Compare the covering email, README, architecture note, validation record and current live behavior. Correct differences in challenge title, application stack, links, access requirements and test counts. Distinguish historical facts from current observations and implemented work from proposed improvements. Keep contact details in the private email rather than the public codebase. Link the actual selected conversation, and label retrospective prompt examples separately.

Acceptance: a reviewer can reproduce the claimed workflows and understand their limits. The submission does not adopt a friend's architecture, feature claims, links or test results.

## 4. Corrections recorded during the actual build

The examples below summarize observed issues. They are not additional conversation messages or claims that the applicant independently performed each code change.

| Observed issue | Recorded correction | Lesson |
|---|---|---|
| Windows temporary-directory access interrupted API tests | The check runner used fresh workspace-local scratch paths | Environment failures should be separated from product failures |
| The NSE endpoint redirected to its official .in host | The verified redirect target was supported | Source adapters need explicit redirect handling |
| PDF requests needed the Windows certificate store | System trust-store verification was used | A certificate problem is not a reason to disable TLS verification |
| Transcript discovery depended on nested page markup | Discovery handling was corrected and exercised with an unseen company | Test outside the curated demo set |
| Embedded fonts affected PDF extraction | Font support was added and the end-to-end probe repeated | Successful downloading is not the same as readable evidence |
| An attested introduction path was not sufficiently prioritized | Its contextual ranking boost was adjusted | Relevance should reflect the strength of relationship evidence |
| A saved market observation could depend on later session/rule changes | Saved observations retained their snapshot | Persistence should match user expectations |
| A transcript-derived metric was labelled as an annual-report source | The displayed source kind was corrected | Citation labels need the same attention as numerical values |
| Old prices remained visible while switching modes | Prior-mode values were cleared during loading | A transient display can still mislead a user |
| A visitor in another browser encountered a token prompt | Explicit public-demo mode was added and checked without credentials | Test the reviewer's first visit, not just the developer's signed-in tab |
| Some covering material still referred to old access/test details | Current access wording and counts were reconciled | Handoff documentation is part of the delivered behavior |

Retrospective correction example:

> The metric's underlying evidence is a call transcript, but its link label says Annual report. Trace the source kind from the API response to the rendered label. Correct the label without changing the fact, and add a regression assertion for the transcript case.

Retrospective correction example:

> A fresh visitor sees the server-token dialog even though this assessment demo should be public. Check server configuration, health metadata, middleware and frontend initialization together. Add an explicit public-demo mode, preserve private defaults, block public model calls, and verify a request with no credentials.

These examples restate recorded problems more precisely. They do not replace or rewrite the original messages in the authentic history.

## 5. Verification evidence and limits

Verification date: **16 November 2026**.

The implementation revision afab03ed2fc9967274806fb61fb214e4985b3f61 passed [GitHub Actions](https://github.com/ayushgoyal771/finn-investment-agent/actions/runs/43771618430). Recorded automated results were **78 Python tests and 11 DOM integration tests, 89 total**. Dependency consistency and JavaScript syntax checks also passed.

A submission-preparation recheck made fresh requests without an Authorization header:

| Check | Observed response |
|---|---|
| Health | HTTP 200; public_demo=true; auth_required=false; model_available=false |
| Demo brief | HTTP 200; eight priority items |
| Synthetic network | HTTP 200; eight profiles |
| Historical Asian Paints research | HTTP 200; four facts and one network match |
| Public repository CI for the implementation revision | Completed successfully |

Earlier hosted browser checks exercised desktop and a 390 x 844 phone-sized viewport. A fresh browser tab loaded the public demo without the token dialog. A physical phone and a formal accessibility audit were not verified.

Earlier local source probes reached Yahoo daily bars, NSE filings, discovery and primary PDFs. Cloud behavior differed: NSE filings and transcript retrieval worked, Yahoo returned HTTP 429, and a large annual report exceeded its processing budget. Those observations are not guarantees of present or future provider availability. The submission-preparation recheck above exercised the historical demonstration, not every live upstream provider.

No credentialed model synthesis call or Docker execution was verified. Passing tests do not establish complete extraction accuracy, production security, current investment suitability or availability of every NSE company.

## 6. What remains unfinished

The prototype intentionally leaves out real-contact import, OCR, intraday prices, delivered mobile notifications, durable background scheduling, full financial-table normalization and a complete four-quarter guidance-versus-delivery ledger.

Production priorities would be:

1. Reliable or licensed feeds with monitored freshness and visible coverage.
2. A quarterly fact store preserving period, units, currency and reporting basis.
3. An evaluated guidance ledger connecting explicit management promises to comparable outcomes.
4. Persistent storage, individual identities and tenant isolation.
5. Consent, retention, deletion/export and encrypted storage for real network data.
6. Isolated document extraction and claim-support evaluation.

Future-work prompt example:

> Start the guidance ledger with one company and four consecutive quarters of original transcripts and result filings. Preserve the promise date, target period, metric, units, reporting basis and evidence page. Match only comparable outcomes. Keep qualitative commentary separate, mark unavailable evidence and require review of each extracted pair before generalizing.

This is proposed work. The existing results comparison remains a synthetic demonstration.

## 7. Reproduction and review

The README explains installation and demonstration steps. The architecture, requirements and validation notes describe the data boundaries and limitations.

Local deterministic checks use the configured Python environment:

    python scripts/check.py
    npm ci
    npm test

The opt-in live probes make outbound requests:

    python scripts/live_probe.py
    python scripts/research_probe.py

Render's free service can sleep and its SQLite state can reset during spin-down, restart or redeployment. Page-reload persistence is different from durable restart persistence. The bundled demonstration is initialized again after startup.

No assessment email has been sent by the assistant. The covering email remains a draft for the applicant to review and send.
