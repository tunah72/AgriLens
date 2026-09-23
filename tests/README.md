# Tests

Current coverage:

- API contract tests for `/health` and `/api/v1/predict`.
- E2E API test for `register/login -> upload image -> prediction -> history` in
  `tests/integration/`.
- Locust load scenario in `tests/load/locustfile.py`; the run procedure and
  acceptance gate are documented in `tests/load/README.md`.

Keep tests lightweight enough for GitHub Actions, and store sample images as small fixtures only.
