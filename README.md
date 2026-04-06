# NMS Cloudflare-First Migration

## Old vs New Architecture

Previous architecture:
- Django backend running as a server/container runtime.
- React frontend served through containerized deployment.
- Container-oriented build and deployment flow.

Current architecture:
- `nms/workers/backend` is the backend Cloudflare Worker project.
- `nms/workers/frontend` is the frontend Cloudflare Worker project.
- Backend and frontend are deployed separately in production.
- Development runs backend and frontend on separate local ports.
- Production database is Cloudflare D1.
- Local development database persistence is stored under `nms/db.dev`.

Docker has been removed from this repository.

## Project Structure

- `nms/workers/backend`: backend Worker source, Wrangler config, D1 schema, backend env files.
- `nms/workers/frontend`: frontend Worker source, Wrangler config, frontend-worker env files.
- `nms/frontend`: React app source; assets are built and served by frontend Worker.
- `nms/build.sh`: primary dev/prod entrypoint.

## Environment Files

Backend Worker:
- `nms/workers/backend/.env.dev`
- `nms/workers/backend/.env.prod`

Frontend Worker:
- `nms/workers/frontend/.env.dev`
- `nms/workers/frontend/.env.prod`

Frontend app build env:
- `nms/frontend/.env.dev`
- `nms/frontend/.env.prod`

All cloud-specific identifiers and secrets are placeholders and must be filled before deployment.

## Frontend/Backend Communication Model

- Frontend Worker serves the SPA and proxies `/api/*` requests to the backend Worker origin.
- Frontend app uses `REACT_APP_API_BASE_URL=/api` so request contracts stay aligned with existing frontend behavior.
- Backend CORS and redirect variables are environment-driven.

## Local Development (No Docker)

`./build.sh dev` does all required local setup and starts separate local services:
- Backend Worker on `http://127.0.0.1:8787`
- Frontend Worker on `http://127.0.0.1:8788`
- Local D1 persistence under `nms/db.dev`

Run:
```bash
cd nms
./build.sh dev
```

## Production Deployment (Separate Workers + D1)

`./build.sh prod` performs:
- frontend asset build
- backend D1 schema migration (remote)
- backend Worker deployment
- frontend Worker deployment

Run:
```bash
cd nms
./build.sh prod
```

Optional target env override:
```bash
cd nms
CLOUDFLARE_ENV=prod ./build.sh prod
```

## Required Cloudflare Configuration

Update both Wrangler files before deploy:
- `nms/workers/backend/wrangler.toml`
- `nms/workers/frontend/wrangler.toml`

Set real values for:
- `account_id`
- worker names
- routes / zone names
- D1 `database_id` and `preview_database_id`
- backend/frontend origin vars

## D1 Setup Notes

Backend schema file:
- `nms/workers/backend/schema.sql`

Used by build flow:
- local migration in `dev`
- remote migration in `prod`

## Cloudflare-Specific Limitations

- Cloudflare Worker runtime does not execute full OS-level network binaries the same way as a full host runtime.
- Where Worker runtime constraints apply, the backend preserves external API shape and responds explicitly.
- If strict parity is required for host-level diagnostics execution, that requires an external execution service integrated behind existing API contracts.
