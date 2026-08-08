# data_platform v0.2.0

`data_platform` is the durable storage boundary for the v3 system. It receives
artifacts identified by `source_intake` and stores them in a controlled root.
It does not acquire sources, interpret content, create knowledge, or make
trading decisions.

This first release provides:

- a storage contract for source artifacts,
- safe source and relative-path validation,
- a filesystem-backed artifact store with staging promotion,
- SHA-256 and size metadata for every stored artifact,
- a SQLite catalog for source and artifact status,
- a workflow that moves available artifacts from staging only when the source
  manifest is complete.
- a reconciliation workflow that is safe to repeat and removes stale durable
  copies for incomplete sources.
- a workflow that registers source links as `not_ready` catalog entries without
  creating or copying any artifact.

The filesystem store is the binary layer and the SQLite catalog is the first
structured metadata layer. Qdrant for semantic retrieval remains a later layer
owned by knowledge processing and can be added without changing the source
intake contract.

Incomplete sources remain in `data/raw/source_intake` for retry. Complete
sources are promoted to `data/artifacts`; the normal persistence path does not
keep a second staging copy. Repeating the promotion does not download or copy
the source again, and the catalog is kept aligned with the actual storage
location.
The module does not create temporary project files or one-off migration data.
