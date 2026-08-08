# Decision 0001: documentation and tooling boundaries

Status: accepted

## Decision

Permanent architecture and process documentation lives in v3 under `docs/`.
Module-specific behavior remains in each module's `README.md`. Agent Atlas is
used for context and scope control. GitHub is a later collaboration and CI
layer, not a prerequisite for the local module work.

## Reason

This keeps the project understandable without mixing source data, generated
outputs, temporary migration files or one-off experiments into the codebase.
It also makes the current limitation of the v2 Atlas index explicit instead of
giving a false impression that v3 is already fully governed by it.
