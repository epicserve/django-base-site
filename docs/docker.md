# Using Docker

The Django Base Site uses Docker Compose for local development. Install [Docker](https://docs.docker.com/engine/installation/), then follow the [README](https://github.com/epicserve/django-base-site#installation) to get a project running.

## Services

`compose.yml` defines the following services, all with healthchecks:

| Service    | Image                                | Notes                                                                  |
|------------|--------------------------------------|------------------------------------------------------------------------|
| `db`       | `postgres:17`                        | Postgres 17. Volume `postgres_data`.                                   |
| `redis`    | `redis:7.0`                          | Cache + Celery broker. Append-only enabled.                            |
| `mailpit`  | `axllent/mailpit`                    | Local SMTP capture. Web UI at http://localhost:8025                    |
| `minio`    | `minio/minio:latest`                 | S3-compatible media storage. Console at http://localhost:9001          |
| `web`      | `epicserve/django-base-site:python`  | Django dev server. Runs migrations + `ensure_s3_bucket` on startup.    |
| `worker`   | same as web                          | Celery worker.                                                         |
| `frontend` | `epicserve/django-base-site:bun`     | bun running the Vite dev server. HMR exposed at http://localhost:3000  |

The `web` and `frontend` containers run as `${HOST_UID:-1000}:${HOST_GID:-1000}` so bind-mount writes don't end up root-owned.

## Frontend Asset Build

`docker compose up` starts the `frontend` service, which runs `bun run dev` (Vite + HMR on port 3000). The Django SPA shell template injects the Vite client; assets reload on save. To build production assets manually:

```bash
docker compose run --no-deps --rm frontend bun run build
```

`just build_frontend` does this plus `collectstatic`.

## Debugging

### Localhost vs 127.0.0.1

Always load the app at **http://localhost:8000/**, not http://127.0.0.1:8000/. WebAuthn passkey enrollment rejects bare IP addresses as Relying Party IDs. The `.env` defaults `SITE_DOMAIN=localhost:8000` for this reason.

### PyCharm

Follow [JetBrains' Docker Compose interpreter guide](https://www.jetbrains.com/help/pycharm/using-docker-compose-as-a-remote-interpreter.html). See [debugging.md](debugging.md) for the full setup.

### VS Code / Neovim / DAP

`just start_with_debugpy` starts the web container with debugpy listening on `:5678`. Attach from any DAP client. See [debugging.md](debugging.md).

## Volumes

| Volume                              | Contents                                                |
|-------------------------------------|---------------------------------------------------------|
| `django-base-site_postgres_data`    | Postgres data files                                     |
| `django-base-site_redis_data`       | Redis append-only log                                   |
| `django-base-site_minio_data`       | MinIO bucket storage                                    |
| `django-base-site_node_modules`     | bun-managed `node_modules` for the frontend container   |

If you change `package.json` and the frontend container fails to find a new dep, the `node_modules` volume is stale. Fix:

```bash
docker compose down
docker volume rm django-base-site_node_modules
docker compose up -d
```

If you change `pyproject.toml`, rebuild the web image:

```bash
docker compose build web
docker compose up -d --force-recreate web
```

## Common Commands

| Command                                     | Description                                                       |
|---------------------------------------------|-------------------------------------------------------------------|
| `just start`                                | `docker compose up`                                               |
| `just start_with_debugpy`                   | Same with `USE_DEBUGPY=true` for remote debugging                 |
| `just stop`                                 | `docker compose down -t 0`                                        |
| `just build`                                | Rebuild images, drop the node_modules volume, re-collectstatic    |
| `docker compose ps`                         | List running services                                             |
| `docker compose logs -f <service>`          | Tail logs for a service                                           |
| `docker compose exec web ./manage.py shell` | Open a Django shell inside the web container                      |
| `docker volume ls`                          | List Docker volumes                                               |

## Common Gotchas

- **Start with `just start` / `docker compose up`** — `docker compose run web ./manage.py runserver` won't expose the port to the host.
- **Stale `node_modules` volume.** Docker only seeds named volumes from the image on first creation. After a `bun install` that adds a new package, drop the volume (above) and bring the stack back up.
- **bun lockfile.** Once `bun install` produces `bun.lock`, commit it. The Dockerfiles use plain `bun install` so first-build works without the lockfile; switch to `bun install --frozen-lockfile` once you've committed `bun.lock` for reproducible prod builds.
- **MinIO endpoint URL split.** `MEDIA_S3_ENDPOINT_URL` (Docker-internal, e.g. `http://minio:9000`) and `MEDIA_S3_URL_ENDPOINT_URL` (browser-facing, e.g. `http://localhost:9000`) must be distinct. The custom `apps.base.storage.S3MediaStorage` rewrites generated URLs.

## References

- [A Brief Intro to Docker for Djangonauts](https://www.revsys.com/tidbits/brief-intro-docker-djangonauts/)
- [bun in Docker](https://bun.sh/guides/ecosystem/docker)
