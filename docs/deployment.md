# Free Render deployment

The owner selected Render's **$0 free demo hosting**. This deployment has one Python web service and no paid disk, database, worker or model integration. SQLite changes can be lost when the free service sleeps, restarts or redeploys. The bundled synthetic demonstration remains available after startup.

Live app: https://finn-investment-agent-ayush.onrender.com

Repository: https://github.com/ayushgoyal771/finn-investment-agent

The service was created through Render's Git Provider flow under the owner's existing account. It uses the exact commands below and deploys subsequent commits after GitHub checks pass. Access details are saved only in the owner's ignored local `artifacts/render-access.env`, not in this repository.

The root `render.yaml` contains the reusable deployment configuration:

- Python 3.12, selected by `.python-version`.
- Build: `pip install -r requirements.txt -c backend/requirements.lock`.
- Start: `python run.py --host 0.0.0.0`.
- Health check: `/api/health`.
- Free compute plan; background refresh disabled.
- A Render-generated `FINN_ACCESS_TOKEN`; no secret is stored in the repository.

The launcher reads Render's `PORT`. Unless `FINN_ALLOWED_HOSTS` explicitly overrides it, the backend adds only the exact hostname in Render's `RENDER_EXTERNAL_HOSTNAME` to its local host allowlist. Other Render tenants are not trusted.

The frontend and API share the same service and HTTPS origin. There is no separate frontend build or CORS configuration. The service initializes its own SQLite tables and demo records at startup.

For dashboard-based creation, choose **Python 3** rather than Docker and copy the commands above. Generate a random `FINN_ACCESS_TOKEN` in Render's environment settings, keep `FINN_BACKGROUND_LIVE=false` (the application default), and leave `FINN_DB_PATH` unset. Render's default writable project directory will hold the ephemeral database.

For Blueprint-based creation, connect this repository and select the checked-in `render.yaml`. Render generates the workspace token. Retrieve it from the service's environment page and use it to unlock FINN. Treat it as an access credential; do not add it to a README or public issue.

Verified after deployment: protected login, desktop and phone-viewport rendering, leadership and results details, bookmark persistence across page reload, historical evidence research, expertise search and preference saves. HCLTECH returned live page-cited transcript evidence with an explicit annual-report timeout warning. NSE filings loaded. Yahoo's daily bars returned HTTP 429 for this cloud instance; the UI shows those observations as unavailable. These limits are recorded rather than replaced with fictional data. The free plan does not provide durable saved state.

Hosting reference: https://render.com/docs/free

Blueprint reference: https://render.com/docs/blueprint-spec
