# frontend v0.2.0

The first frontend release is a small web application for `source_intake`.
It shows persisted source status and lets an operator register a source and
select the acquisition operations to run. It also provides a background batch
action for processing all pending sources with live progress status and a
read-only readiness popover showing persisted artifact states. The source form
supports both URL input and local file upload, with the default selected from
the source type.

The application is deliberately thin. It calls source intake workflows,
`data_platform` storage and the SQLite catalog; it does not contain provider,
knowledge-processing or trading logic. The standard-library server is a
development foundation and can later be replaced by a dedicated web runtime
without changing the module contracts.

Run from the v3 root:

```text
PYTHONPATH=. /path/to/python -m modules.frontend.source_intake_app --port 8765
```
