# Testing policy

Tests are kept with the module they protect:

```text
modules/<module>/tests/
```

The current reusable suite covers:

- `source_intake`: 21 tests for acquisition, contracts, manifests, local
  files, idempotence and agent coordination.
- `data_platform`: 9 tests for storage, promotion, reconciliation, catalog and
  incomplete sources.
- `frontend`: 4 tests for status API, batch processing and local upload.
- `system_core`: 12 tests for versions, policies, readiness, dependencies and
  lifecycle.

## Rules

- Keep tests that protect a repeatable behavior.
- Do not keep one-off diagnostic scripts or temporary test data in the project.
- Prefer a small number of focused tests over broad tests with unclear purpose.
- Test a module's public boundary and its important failure states.
- Add an integration test when a change crosses a module boundary.
- A module is not `stable` only because its tests pass; scope and contracts must
  also be reviewed.

Run the current foundation suite from the v3 root:

```text
PYTHONPATH=. /path/to/python -m pytest -q \
  modules/source_intake/tests \
  modules/data_platform/tests \
  modules/frontend/tests \
  modules/system_core/tests
```
