# JWT authentication (production)

## Overview

When `RYW_AUTH_MODE=jwt`, the API ignores `X-Role` for authorization and expects:

```http
Authorization: Bearer <token>
```

## HS256 (development)

1. Set `RYW_JWT_SECRET` to a long random string.
2. Issue tokens with payload including `role`: `analyst` | `ops` | `admin` (claim name overridable via `RYW_JWT_ROLE_CLAIM`).

Example payload:

```json
{ "role": "ops", "sub": "user-123" }
```

## Header mode (demos only)

Default `RYW_AUTH_MODE=header` uses `X-Role`. **Do not expose this mode on the public internet.**

See repository `docs/adr/0001-auth-strategy.md`.
