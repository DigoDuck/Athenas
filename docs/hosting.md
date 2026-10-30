# Hosting on Railway

The hosted Athenas (D-042, D-043) runs on Railway as three services in one project: `web` (nginx with
the built frontend, the only public one), `backend` (Django and gunicorn) and `Postgres`. The
browser sees one origin; nginx forwards `/api/` to the backend over Railway's private network.
The same images run use mode through `docker-compose.yml`.

No real data goes in until login (T2), data per person (T3) and the restore drill (T4) are on
`main` (`docs/plan-testers.md`).

## One-time setup in the Railway dashboard

Everything here works from a phone browser. Service names matter: the variables below refer to
`web`, `backend` and `Postgres` by name.

1. New project, "Deploy from GitHub repo", `DigoDuck/Athenas`. Rename the service it creates to
   `backend`. Do not generate a public domain for it.
2. In the project, add a PostgreSQL database. Keep its name `Postgres`.
3. Add the same GitHub repo again as a second service and rename it `web`. In its settings, set
   Root Directory to `frontend`, generate a Railway domain (target port 80), and set the
   healthcheck path to `/api/health/`.
4. `backend` variables:

   ```text
   RAILWAY_DOCKERFILE_PATH=backend/Dockerfile
   DJANGO_SECRET_KEY=<at least 50 random characters from a password manager>
   DJANGO_ALLOWED_HOSTS=${{web.RAILWAY_PUBLIC_DOMAIN}},healthcheck.railway.app
   POSTGRES_DB=${{Postgres.PGDATABASE}}
   POSTGRES_USER=${{Postgres.PGUSER}}
   POSTGRES_PASSWORD=${{Postgres.PGPASSWORD}}
   POSTGRES_HOST=${{Postgres.PGHOST}}
   POSTGRES_PORT=${{Postgres.PGPORT}}
   ```

5. `web` variables:

   ```text
   BACKEND_URL=http://${{backend.RAILWAY_PRIVATE_DOMAIN}}:8000
   ```

6. Project settings, Environments: turn on PR environments. If "focused" PR environments is
   offered, turn it off: a preview where only `web` deploys has no backend to proxy to.
7. In `web` and `backend` settings, turn on "Wait for CI" where Railway offers it, so a red PR
   never deploys.

Each service builds the last stage of its Dockerfile (`use`). The backend runs its migrations on
every start, as use mode does.

## Previews

Each pull request gets its own environment with its own empty database and a `web` domain that
Railway posts on the PR. The thread runs its smoke test (health, the main screens) against it
before asking for a merge. The environment is deleted when the PR closes.

## When something breaks

- Roll back: open the service, Deployments, pick the last good deployment, Redeploy. This works
  from a phone and changes no code.
- `502` from `/api/` with a healthy backend: the private network may be IPv6 only in this
  environment. Add `GUNICORN_BIND=[::]:8000` to `backend` and redeploy.
- `400 Bad Request` from `/api/`: the domain is missing from `DJANGO_ALLOWED_HOSTS`.
