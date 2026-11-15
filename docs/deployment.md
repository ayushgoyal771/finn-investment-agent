# Founding AI Engineer: public free Render demo

Ayush Goyal's ENAM Founding AI Engineer prototype runs on one free native Python service, serving the frontend and API together.

- App: https://finn-investment-agent-ayush.onrender.com
- Source: https://github.com/ayushgoyal771/finn-investment-agent
- Access: opens directly without a login or server token.

The owner requested public access to make the assessment easy to try. The service uses `FINN_PUBLIC_DEMO=true`. This explicitly bypasses private-workspace token checks, clears old tokens from browser session storage, and disables all model synthesis, even if a model key is configured. All profiles and relationships are synthetic; saved signals, preferences and contact dates are shared demonstration state. Do not use this mode with real contact data.

## Service configuration

- Runtime: Python 3.12, selected by `.python-version`.
- Build: `pip install -r requirements.txt -c backend/requirements.lock`.
- Start: `python run.py --host 0.0.0.0`.
- Health check: `/api/health`.
- Environment: `FINN_PUBLIC_DEMO=true`, `FINN_BACKGROUND_LIVE=false`, `FINN_POLL_SECONDS=900`, `PYTHONUNBUFFERED=1`.
- No paid disk, managed database or model key.
- GitHub `main`; automatic deployment after checks pass.

The checked-in `render.yaml` represents this public-demo configuration. The existing Git Provider service also needs `FINN_PUBLIC_DEMO=true` in its Render environment settings; changing the YAML alone does not update a service created without a Blueprint.

The launcher reads Render's assigned `PORT`. The backend allows the exact `RENDER_EXTERNAL_HOSTNAME`, not other Render tenants. Trusted-host checks, foreign-origin write rejection, request limits and source-fetch boundaries remain enabled. An old `FINN_ACCESS_TOKEN` may remain configured but is ignored only while explicit public-demo mode is on.

## Storage and source limits

Render's free service can sleep. SQLite state may reset during spin-down, restart or redeployment; bookmark persistence after a page reload does not establish durable storage. Bundled demonstrations initialize after startup.

NSE filings and live page-cited transcript retrieval were verified during earlier hosted checks. Yahoo returned HTTP 429 from this instance and a large annual report timed out; the interface reports those limits without fictional fallback. These are point-in-time checks, not source-availability guarantees.

## Private installation

For private hosting, set `FINN_PUBLIC_DEMO=false`, configure a long random `FINN_ACCESS_TOKEN` and approved hosts, then redeploy. Remote private access still requires that token. A private token does not provide multi-tenant isolation: this remains one shared workspace.
