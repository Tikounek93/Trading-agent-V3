# knowledge_processing v1.2.0

`knowledge_processing` converts already acquired source artifacts into
structured, traceable and advisory knowledge. It does not download sources,
create a strategy, approve a strategy or trade.

## What it does

- reads subtitle or transcript artifacts selected by `SourceCatalog`;
- creates a canonical timeline and semantic chunks;
- samples readable source videos into frame and OCR sidecars and attaches them
  by timestamp;
- extracts domain events, concepts, setup stages and traceable knowledge units;
- assigns an advisory relevance score with explicit reasons;
- validates timing, provenance, required fields and the module boundary;
- stores a current JSON projection plus append-only history per source;
- processes one source or all ready catalog sources repeatedly and idempotently.

The pipeline is deterministic and text-first. OCR production is a replaceable
optional tool inside this module: it uses OpenCV for video decoding and
Tesseract for text recognition. If those dependencies are unavailable, or the
video cannot be decoded, processing continues and the artifact records no OCR
for that source instead of inventing data.

## Input and output

The direct workflow accepts a local subtitle artifact and optional frame/OCR
records. The catalog workflow resolves those inputs from `SourceCatalog` and
the promoted artifact root. When a video is available but no sidecars exist,
it creates sampled frame and OCR sidecars under that source's raw artifact
directory. A missing subtitle or transcript blocks that source without
creating an incomplete knowledge artifact.

Knowledge output is stored under `data/knowledge/<source_id>/knowledge.json`.
Every changed projection also receives a timestamped file under that source's
`history` directory. Raw source files and the source catalog are never
modified by this module.

The output describes evidence, concepts, stages and relevance. It never
contains execution, approval, broker or strategy-activation authority.

## Repeatable operation

```text
PYTHONPATH=. /path/to/python scripts/process_knowledge_sources.py
```

Use `--knowledge-root /temporary/path` for a disposable verification run.
The generated knowledge dataset is operational data and is not committed to
the repository.
