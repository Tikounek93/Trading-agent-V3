# Architecture

Trading Agent v3 is a modular system for preparing knowledge, building and
testing trading strategies, and later operating an approved strategy. Modules
have explicit boundaries. An agent coordinates work inside a module, a tool
performs a focused operation, and a workflow defines the order and conditions
of a process.

## Current implemented flow

```text
operator or source list
        |
        v
source_intake -- registers sources and acquires source artifacts
        |
        v
data_platform -- stores artifacts and catalog metadata
        |
        v
knowledge_processing -- planned next consumer
```

The current v3 slice deliberately stops before knowledge processing and
trading logic. It must be possible to replace the web interface, storage
implementation or provider adapter without changing the source and artifact
contracts.

## Boundary rules

- `source_intake` does not interpret content or make trading decisions.
- `data_platform` does not download sources or create knowledge.
- `frontend` is an operator surface, not a domain decision-maker.
- `system_core` controls lifecycle, readiness, modes and manifests; it does
  not analyze markets.
- Planned strategy modules must consume explicit contracts rather than reach
  into another module's private files.

## Storage flow

Incomplete source artifacts stay in `data/raw/source_intake` so acquisition can
be retried. A complete source manifest promotes artifacts into
`data/artifacts`. Promotion moves the file and records size and SHA-256 in the
SQLite catalog. The normal path does not keep a second staging copy.

## Planned information flow

```text
source_intake
    -> data_platform
    -> knowledge_processing
    -> strategy_blueprint
    -> strategy_engine
    -> setup_candidate
    -> execution / trade_management
    -> trading_journal and decision_journal
```

The planned modules are documented as boundaries only. They are not considered
implemented until their contracts, implementation and module-level verification
are present.
