# system_core v0.1.0

`system_core` is the deterministic control plane for Trading Agent v3.

This first release provides:

- module manifests and public contract declarations,
- module registration and in-memory dependency tracking,
- explicit module lifecycle states,
- backtest, paper and live mode validation,
- human approval enforcement for live mode,
- basic contract compatibility checks,
- health state tracking,
- reproducible run manifests,
- startup, shutdown and read-only health workflows.

The first release does not contain:

- market or trading logic,
- an AI agent,
- broker or MT5 access,
- database persistence,
- a distributed event broker,
- automatic retry or recovery.

State is intentionally held in memory. Persistence belongs to `data_platform` in a
later version. Callers provide timestamps and identifiers so the core does not read
the wall clock or create hidden local state.
