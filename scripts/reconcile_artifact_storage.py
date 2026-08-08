"""Promote complete source artifacts and clean durable duplicates."""

from pathlib import Path

from modules.data_platform.catalog import SourceCatalog
from modules.data_platform.storage import FileSystemArtifactStore
from modules.data_platform.workflows import reconcile_artifact_storage


def main() -> None:
    project_root = Path(__file__).resolve().parents[1]
    result = reconcile_artifact_storage(
        SourceCatalog(project_root / "data" / "catalog" / "source_catalog.sqlite3"),
        project_root / "data" / "raw" / "source_intake",
        FileSystemArtifactStore(project_root / "data" / "artifacts"),
    )
    print(
        f"promoted={len(result.promoted_source_ids)} "
        f"staging={len(result.staging_source_ids)} "
        f"removed_duplicates={result.removed_duplicate_count}"
    )


if __name__ == "__main__":
    main()

