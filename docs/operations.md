# Operations

These procedures belong to the current source-intake slice. They are meant to
be repeatable and do not create migration copies or temporary project data.

## Start the operator application

From `/Users/martincerny/trading_agent_v3`:

```text
PYTHONPATH=. /path/to/python -m modules.frontend.source_intake_app --port 8765
```

Open `http://127.0.0.1:8765` in a browser. Use another free port if the
requested port is already occupied.

## Register source links

The source-link import creates catalog records only. It does not download
anything. Acquisition is a separate explicit operation.

## Reconcile artifact storage

After changing storage semantics or recovering from an interrupted run:

```text
PYTHONPATH=. /path/to/python scripts/reconcile_artifact_storage.py
```

The operation is repeatable. Complete sources are promoted to
`data/artifacts`; incomplete sources remain in `data/raw/source_intake`.

## Data locations

- `data/raw/source_intake` - incomplete or retryable staging artifacts.
- `data/artifacts` - promoted durable artifacts.
- `data/catalog/source_catalog.sqlite3` - source and artifact metadata.

Downloaded media and catalog data are project data, not documentation and not
test fixtures.
