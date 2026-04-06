# NMS Cloudflare Architecture (Organized Env Layout)

## Final Scenario

Production:
- `frontend-worker` (Cloudflare Worker)
- `backend-worker` (Cloudflare Worker)
- `diagnostics-service` (Django executor on Cloudflare Containers/host compute)
- Worker-side production DB: Cloudflare D1

Development:
- frontend worker: `http://127.0.0.1:8788`
- backend worker: `http://127.0.0.1:8787`
- diagnostics Django service: `http://127.0.0.1:8000`
- local Worker D1 persistence: `nms/db.dev`
- local Django sqlite: `nms/db.dev.sqlite3`

## Organized Env Folders

All source env files are organized under:
- `nms/config/env/backend`
- `nms/config/env/frontend`
- `nms/config/env/diagnostics`

Each contains both editable runtime files and examples:

Backend:
- `nms/config/env/backend/.env.dev`
- `nms/config/env/backend/.env.prod`
- `nms/config/env/backend/.env.dev.example`
- `nms/config/env/backend/.env.prod.example`

Frontend app build:
- `nms/config/env/frontend/.env.dev`
- `nms/config/env/frontend/.env.prod`
- `nms/config/env/frontend/.env.dev.example`
- `nms/config/env/frontend/.env.prod.example`

Frontend worker runtime:
- `nms/config/env/frontend/.env.worker.dev`
- `nms/config/env/frontend/.env.worker.prod`
- `nms/config/env/frontend/.env.worker.dev.example`
- `nms/config/env/frontend/.env.worker.prod.example`

Diagnostics service:
- `nms/config/env/diagnostics/.env.dev`
- `nms/config/env/diagnostics/.env.prod`
- `nms/config/env/diagnostics/.env.dev.example`
- `nms/config/env/diagnostics/.env.prod.example`

## How build.sh Uses Env Files

`./build.sh dev` and `./build.sh prod` now:
1. load env from `nms/config/env/**`
2. sync runtime files automatically into:
   - `nms/workers/backend/.env.dev|.env.prod`
   - `nms/workers/frontend/.env.dev|.env.prod`
   - `nms/frontend/.env.dev|.env.prod`
3. run the corresponding dev/prod flow

If a runtime env file in `config/env` is missing, `build.sh` auto-creates it from its `.example` template.

## Commands

Local development (all services):
```bash
cd nms
./build.sh dev
```

Production deploy flow:
```bash
cd nms
./build.sh prod
```

## Diagnostics Execution Path

- frontend -> backend (`/api/dashboard/`)
- backend worker -> diagnostics executor (`/dashboard/executor-dashboard/`) using `DIAGNOSTICS_EXECUTOR_TOKEN`
- diagnostics executor runs ping/traceroute/dns/snmp/mtr and returns existing response contract

## Production Diagnostics Deployment Hook

`./build.sh prod` calls:
- `nms/scripts/deploy_diagnostics_service.sh`

Set in `nms/config/env/diagnostics/.env.prod`:
- `DIAGNOSTICS_DEPLOY_CMD` with your Cloudflare Containers deployment command.

## Important Placeholders to Fill

- Cloudflare `account_id`, routes, and D1 IDs in both wrangler files
- Azure SSO credentials
- `DIAGNOSTICS_EXECUTOR_URL`
- `DIAGNOSTICS_EXECUTOR_TOKEN`
- `DIAGNOSTICS_DEPLOY_CMD`
