# NMS (Frontend Worker + D1)

## What Runs Where
- Production: Cloudflare Worker serves the SPA and `/api/*` (D1 in prod)
- Local dev: same worker via `wrangler dev` (D1 persisted in `nms/dev.db`)
- Diagnostics execution: `/api/dashboard` proxies to the Django executor (`nms/manage.py`)

## Run

Local development (worker + diagnostics):
```bash
bash run.sh dev
```

Production deploy (migrate D1 + deploy worker + diagnostics hook):
```bash
bash deploy.sh prod
```

## Env
- Edit example templates in `nms/config/env/**.example`
- `bash run.sh dev` creates missing env files from examples automatically
- To reset/re-copy examples over existing env files: `NMS_ENV_FROM_EXAMPLES=1 bash run.sh dev`

## Required Setup
- Fill Cloudflare `account_id`, routes, and D1 IDs in `nms/workers/frontend/wrangler.toml:1`
- Set diagnostics executor URL/token in `nms/config/env/frontend/.env.worker.*.example:1`
