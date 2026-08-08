# knowledge_processing v0.1.0

knowledge_processing transforms already acquired source artifacts into
structured, traceable and advisory knowledge. It does not download sources,
build a strategy, approve a strategy or trade.

This first candidate release ports the deterministic core of the useful v2
extraction behavior:

- VTT subtitle parsing and timeline creation,
- semantic chunking with transcript and event provenance,
- topic and setup-stage enrichment,
- knowledge-unit extraction,
- advisory relevance scoring.

OCR, video frame extraction, video decoding, external AI calls and database
persistence are intentionally separate follow-up boundaries. OCR and frame
references can already travel through the timeline shape when supplied by a
future tool.

## Input and output

The workflow accepts a local subtitle artifact identified by source_id. It
returns an append-only knowledge artifact containing the source identity,
timeline, chunks, knowledge units and advisory scores. Raw source files are
never modified.

The output describes evidence and relevance. It never contains execution,
approval, broker or strategy-activation authority.
