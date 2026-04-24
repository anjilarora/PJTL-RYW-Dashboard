# Roles and authentication

## Roles

The system has three roles, defined in
[code/backend/api/schemas.py](../../backend/api/schemas.py) as
`Role = Literal["admin", "ops", "analyst"]`. They are ordered:

```
analyst(1) < ops(2) < admin(3)
```

Every protected route depends on
[code/backend/api/auth.py](../../backend/api/auth.py) `get_role`, which
returns the caller's role based on `RYW_AUTH_MODE`. Routes then call
`require_role(minimum, actual)` which 403s on underprivileged callers.

### What each role can do

| Capability | analyst | ops | admin |
|---|:-:|:-:|:-:|
| Read KPI catalog (`/api/v1/kpis`) | yes | yes | yes |
| Run viability (`/api/v1/viability/evaluate`) | yes | yes | yes |
| Run inference (`/api/v1/inference/*`) | yes | yes | yes |
| Upload workbook (`/api/v1/jobs/upload`) | yes | yes | yes |
| Operations demo CRUD (`/api/v1/operations/*`) | - | yes | yes |
| Metrics admin (`/api/v1/admin/metrics`) | - | - | yes |

If a role is added, do it in the `ROLE_ORDER` dict in
[auth.py](../../backend/api/auth.py), the `Role` literal in
[schemas.py](../../backend/api/schemas.py), and any frontend role controls
that may be enabled for the deployment.

## Auth modes

Selected by `RYW_AUTH_MODE` in
[code/backend/api/config.py](../../backend/api/config.py):

### `header` (default, demo-only)

- Caller sets `X-Role: analyst | ops | admin`.
- Absent header -> `analyst`.
- Unknown role -> 401.
- **This is not authentication.** Any client can forge any role.
- Only suitable for demos behind a trusted proxy.

### `jwt` (production)

- Caller sends `Authorization: Bearer <token>`.
- The token is decoded with `RYW_JWT_SECRET` using
  `RYW_JWT_ALGORITHM` (default `HS256`).
- The role is read from the `RYW_JWT_ROLE_CLAIM` claim (default
  `"role"`).
- Decode failure -> 401. Unknown role -> 403.

## Migration path: header -> JWT

1. Stand up your IdP (Auth0, Keycloak, Cognito, etc.).
2. Configure the IdP to issue the `role` claim in the JWT.
3. Export `RYW_AUTH_MODE=jwt`, `RYW_JWT_SECRET=...`, and optionally
   `RYW_JWT_ALGORITHM`, `RYW_JWT_ROLE_CLAIM`.
4. Update the frontend to attach `Authorization: Bearer ...` instead of
   demo headers. The IdP should remain the source of truth for role claims.
5. Rotate the secret periodically; the backend reads it at process start
   (it is `lru_cache`d), so restart the backend to pick up a new secret.

## X-Internal-Secret

Independent of the auth mode, you can protect every `/api/v1/*` path by
setting `RYW_INTERNAL_API_SECRET`. When set:

- `InternalSecretMiddleware` enforces `X-Internal-Secret: <secret>`.
- `/health` and `/ready` are exempt so Docker health checks continue to
  work.
- The frontend proxy injects the same header from
  `NUXT_INTERNAL_API_SECRET`.

This is the mechanism that prevents direct curl traffic from reaching
the API when both proxy and backend run on the same network.

## Headers summary

| Header | Purpose | When |
|---|---|---|
| `X-Role` | Sets the caller's role in `header` mode. | Demo mode only. |
| `Authorization: Bearer <jwt>` | Carries the role and identity. | JWT mode. |
| `X-Internal-Secret` | Shared secret between proxy and API. | When `RYW_INTERNAL_API_SECRET` is set. |
| `X-Request-Id` | Attached by `RequestContextMiddleware` if absent; echoed back. | Always. |

See [ops/security-todos.md](../ops/security-todos.md) for the pre-deploy
checklist.
