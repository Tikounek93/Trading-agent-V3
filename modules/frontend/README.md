# frontend v0.3.0

The frontend is the local operator workspace for the v3 modules. It provides
one application shell with navigation between the currently implemented source
intake and knowledge processing areas. Future strategy and trading areas are
visible as planned destinations but are not active.

## Current workspace

- `Overview` shows catalog, knowledge and correction status.
- `Source Intake` registers sources, acquires artifacts and inspects readiness.
- `Knowledge Processing` starts processing, lists generated artifacts and
  explores timelines, chunks and knowledge units.
- `Knowledge Processing` also opens operator corrections for the selected
  source in an append-only layer without modifying generated knowledge or raw
  source artifacts.
- `Processing History` shows current pipeline versions, counts and correction
  totals per processed source.

The application remains a thin composition layer. Source acquisition,
catalog access, knowledge processing and correction persistence live in their
own modules; the frontend only exposes their public workflows over a local HTTP
API.

Run from the v3 root:

```text
PYTHONPATH=. /path/to/python -m modules.frontend.source_intake_app --port 8765
```
