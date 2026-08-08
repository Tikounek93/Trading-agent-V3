# Contracts

Contracts are the stable language between modules. They are represented by
interfaces, dataclasses, enums or documented payloads in the owning module.
They are not only prose documentation.

## Current contracts

- `system_core` provides module manifests, semantic versions, lifecycle
  states, runtime modes, health and run manifests.
- `source_intake` provides source records, artifact records, acquisition plans
  and source manifests.
- `data_platform` provides storage keys, stored-artifact receipts and the
  SQLite source catalog.
- `frontend` consumes the source-intake and data-platform interfaces; it does
  not define provider or trading contracts.

## Contract rules

- A consumer uses the public contract of a provider, not its private module
  implementation.
- Contract changes require a version decision and focused tests.
- A module may expose a partial implementation while its status is
  `candidate`; consumers must not treat it as stable without an explicit
  readiness check.
- IDs and relative paths must remain reproducible and safe.
- Data provenance must survive every hand-off through source and artifact IDs.

The first implementation keeps contracts in source code next to their owning
module. This document explains their role; it is not a duplicate definition
of the interfaces.
