"""Register the v2 video URL seed in the v3 source catalog."""

from __future__ import annotations

import argparse
from datetime import UTC, datetime
from pathlib import Path

from modules.data_platform.catalog import SourceCatalog
from modules.data_platform.workflows import register_source_links
from modules.source_intake.registry import SourceRegistry


def main() -> None:
    project_root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description="Import source links without downloading")
    parser.add_argument(
        "--links-file",
        type=Path,
        default=project_root / "data" / "source_intake" / "v2_source_links.txt",
    )
    parser.add_argument(
        "--catalog",
        type=Path,
        default=project_root / "data" / "catalog" / "source_catalog.sqlite3",
    )
    args = parser.parse_args()
    links = tuple(
        line.strip()
        for line in args.links_file.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    )
    result = register_source_links(
        SourceRegistry(),
        SourceCatalog(args.catalog),
        links,
        datetime.now(UTC),
    )
    print(f"imported={len(result.imported_source_ids)} duplicates={len(result.duplicate_source_ids)}")


if __name__ == "__main__":
    main()

