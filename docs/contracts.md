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
- `knowledge_processing` provides a canonical timeline shape, optional
  frame/OCR evidence, and append-only advisory knowledge artifacts with source
  provenance, relevance scores and quality reports.
- `frontend` consumes the source-intake and data-platform interfaces; it does
  not define provider or trading contracts.

## Contract rules

- A consumer uses the public contract of a provider, not its private module
  implementation.
- Contract changes require a version decision and focused tests.
- A module may expose a partial implementation while its status is
  `candidate`; consumers must not treat it as stable without an explicit
  readiness check. The `knowledge_processing` contract is stable at `1.0.0`.
- IDs and relative paths must remain reproducible and safe.
- Data provenance must survive every hand-off through source and artifact IDs.
- Knowledge outputs may describe evidence, concepts, stages and relevance, but
  must not authorize strategy activation, execution or broker actions.
- Knowledge persistence keeps the latest projection at
  `data/knowledge/<source_id>/knowledge.json` and appends changed projections
  to its history directory. Reprocessing identical input is idempotent.

The first implementation keeps contracts in source code next to their owning
module. This document explains their role; it is not a duplicate definition
of the interfaces.
