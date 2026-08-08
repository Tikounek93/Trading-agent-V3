# source_intake v1.1.0

`source_intake` registers knowledge sources and describes the artifacts already
available for each source. It is the first real module connected to the v3
module structure after `system_core`.

Version 0.1.0 established the source and artifact contracts. Version 0.2.0
added explicit acquisition operations. Version 1.0.0 marks the module complete
for its first scope: register, acquire, inspect and hand off source artifacts.

This release provides:

- immutable source and artifact contracts,
- safe source identifiers and relative artifact paths,
- an in-memory source registry,
- a `SourceAcquisitionAgent` that coordinates explicit acquisition plans,
- a reusable source-link import tool that registers URLs without downloading,
- a local-file intake workflow for video, document, note and image sources,
- read-only local artifact inspection,
- source manifest and readiness calculation,
- a small idempotent intake workflow,
- separate video acquisition,
- separate provider metadata acquisition,
- separate VTT subtitle acquisition and filename normalization,
- an explicit acquisition plan and acquisition result for partial failures,
- a complete source manifest handoff contract,
- a `system_core` module manifest.

This release does not parse content, create timelines, run OCR, call AI or write
knowledge data. Those capabilities remain separate boundaries:

- the YouTube provider is isolated behind an adapter and can later be replaced,
- durable storage is delegated to `data_platform` through its artifact-store
  port,
- timeline, chunks and knowledge preparation belong to `knowledge_processing`.

The v2 passive frontend registry and display projections were not copied. Historical
preview files, one-off batch runners and their test ballast were not carried into v3.

The module is stable at `1.1.0` for this boundary. Provider retries, additional
providers and semantic processing belong to later modules or releases.
