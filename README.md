# NMS (Frontend Worker + D1)

## What Runs Where
- Production: Cloudflare Worker serves the SPA and `/api/*` (D1 in prod)
- Local dev: same worker via `wrangler dev` (D1 persisted in `nms/dev.db`)
- Diagnostics execution (prod): `/api/dashboard` returns a stub message on Cloudflare Free (no OS tools in Workers)
- Diagnostics execution (dev): `/api/dashboard` proxies to the local Django executor (`nms/manage.py`)

## Run

Local development (worker + diagnostics):
```bash
bash run.sh dev
```

Production deploy (migrate D1 + deploy worker):
```bash
bash deploy.sh prod
```

Wrangler auth (first time only):
```bash
bash deploy.sh login
bash deploy.sh logout
```

## Env
- Edit example templates in `nms/config/env/**.example`
- `bash run.sh dev` creates missing env files from examples automatically
- To reset/re-copy examples over existing env files: `NMS_ENV_FROM_EXAMPLES=1 bash run.sh dev`

## Required Setup
- Fill Cloudflare `account_id` and D1 IDs in `nms/workers/frontend/wrangler.toml:1`
- If using a custom domain, set `routes` to a zone that exists in your Cloudflare account (otherwise leave routes commented out)
- (Optional) For real diagnostics in prod, set `DIAGNOSTICS_MODE=url` and `DIAGNOSTICS_EXECUTOR_URL`/`DIAGNOSTICS_EXECUTOR_TOKEN` in `nms/workers/frontend/wrangler.toml:1`
