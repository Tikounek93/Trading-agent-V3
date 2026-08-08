"""Process all ready source artifacts into local knowledge artifacts."""

from __future__ import annotations

import json
import argparse
from pathlib import Path
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from modules.data_platform.catalog import SourceCatalog
from modules.knowledge_processing.storage import KnowledgeArtifactStore
from modules.knowledge_processing.workflows import process_ready_sources


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--catalog", type=Path, default=PROJECT_ROOT / "data/catalog/source_catalog.sqlite3")
    parser.add_argument("--artifact-root", type=Path, default=PROJECT_ROOT / "data/artifacts")
    parser.add_argument("--knowledge-root", type=Path, default=PROJECT_ROOT / "data/knowledge")
    args = parser.parse_args()
    result = process_ready_sources(
        SourceCatalog(args.catalog),
        args.artifact_root,
        KnowledgeArtifactStore(args.knowledge_root),
    )
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
