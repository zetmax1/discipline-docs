---
paths:
  - "discipline-back/**"
---

# API and worker rules (discipline-back, Go)
- The user id comes only from the verified access token. Every query on user data filters by it.
- Validate every create AND update field (format, range, enum); updates write only the provided fields.
- Check the DB error before `RowsAffected`: DB errors are 500, not 404.
- Migrations: goose, one new file per change, each with a Down step. Never edit a migration that may have run anywhere. The server refuses to start unless the schema is at the latest version.
- Multi-row writes run in one transaction.
- Outbound HTTP: an `http.Client` with a timeout (there is no shared client), the request context (`http.NewRequestWithContext`), and `io.LimitReader` on response bodies.
- Rate limits and throttles live in Redis. On Redis errors they log and fail open, except `/api/auth/*` and the login throttle, which fail closed with 503.
- Calls to analytics carry the short-lived internal JWT; never forward client query strings or raw bodies.
- Logs are JSON with the request id; never log tokens, passwords, emails or request bodies.
- Responses that the web reads are validated in handler tests against `../discipline/contracts/` with `contracttest.Validate` (`internal/contracttest`; `CONTRACTS_DIR` overrides the path). Example: `internal/handlers/feature_handler_test.go`.
- New features sit behind `FEATURE_<id>` (`config.EnabledFeatures`, served at `GET /api/features`).
- Tests: `go test -race` with httptest. DB/Redis tests skip without `TEST_DATABASE_URL` / `TEST_REDIS_URL`; `make test` sets both, and any skip fails the check.
