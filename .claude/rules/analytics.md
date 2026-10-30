---
paths:
  - "discipline-py/**"
---

# Analytics rules (discipline-py, Python/FastAPI)
- Identity and timezone come only from the internal JWT claims (`sub`, `tz`). No `user_id` parameters anywhere.
- Every number comes from the single metrics module (`app/metrics.py`); no second formula elsewhere.
- Metrics and rules use category **kind**, never category names.
- Every endpoint has a Pydantic response model that matches `../discipline/contracts/`; the contract test (`tests/test_contract.py`) must stay green (`ANALYTICS_CONTRACT` = path to the schema file if the repos aren't side by side).
- Ranges are clamped to "today" in the user's timezone; future blocks never count.
- Return `null` / `insufficient_data` instead of a fake 0.
- No pyplot; charts move to the client in M6.
- Read-only DB access; never write tables owned by the API.
- Tests: pytest. DB tests skip without `TEST_DATABASE_URL`; `make test` sets it, and any skip fails the check. Dependencies pinned in `requirements.txt` (generated from `requirements.in`); dev tools in `requirements-dev.txt`.
