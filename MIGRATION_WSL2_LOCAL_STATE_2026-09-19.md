# OrderScope WSL2 local-state migration inventory

Created: 2026-09-19 (Asia/Tokyo)

## Included in the OrderScope folder

- `var/` — local benchmarks, cross-market observations, and D1 custody evidence (approximately 792 KiB).
- `.wrangler/state/` — local Miniflare cache and D1 SQLite state (approximately 324 KiB).
- `MIGRATION_WSL2_LOCAL_STATE_2026-09-19.sha256` — integrity manifest for the files above.

No separate `ORDERSCOPE_DATA_ROOT` was configured in the inspection process, and no external OrderScope data root was found under the current WSL home. The application default therefore resolves to repository-relative `var/` for a process started from the repository root.

## Deliberately excluded

- `.venv/` and `node_modules/`: platform-specific and must be rebuilt on the destination.
- `.env`, `.env.cloudflare`, and `.dev.vars`: secrets and management credentials must be transferred separately through a secure channel or recreated.
- uv/npm caches and Codex caches.
- Remote Cloudflare D1 data: it remains in Cloudflare and is not a local file-transfer target.

## Copy requirements

1. Stop OrderScope, Uvicorn, Wrangler dev, and Miniflare before copying. They were not running when this inventory was created.
2. Copy the complete OrderScope directory, including hidden `.wrangler/`.
3. Do not omit SQLite `-wal` or `-shm` files from `.wrangler/state/`.
4. Place the destination repository and mutable data on the WSL2 Linux filesystem, for example `~/code/OrderScope`, not under `/mnt/c`, `/mnt/d`, OneDrive, or another synchronized directory.
5. Before starting Wrangler or modifying local data, verify the snapshot from the destination repository root:

   ```bash
   sha256sum --check MIGRATION_WSL2_LOCAL_STATE_2026-09-19.sha256
   ```

6. Rebuild dependencies in destination WSL2. Do not reuse the copied `.venv/` or `node_modules/` if they are present:

   ```bash
   npm ci
   uv sync --locked
   ```

The repository currently has a known `pyproject.toml` / `uv.lock` mismatch involving `httpx2`; resolve and review that lockfile difference before relying on `uv sync --locked` as the destination acceptance gate.
