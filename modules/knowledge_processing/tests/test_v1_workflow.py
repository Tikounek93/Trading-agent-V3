import json
from datetime import UTC, datetime
from pathlib import Path

from modules.data_platform.catalog import SourceCatalog
from modules.knowledge_processing.storage import KnowledgeArtifactStore
from modules.knowledge_processing.tools.validate_knowledge_artifact import (
    validate_knowledge_artifact,
)
from modules.knowledge_processing.workflows import (
    process_catalog_source,
    process_ready_sources,
    process_source,
)
from modules.source_intake.contracts import (
    ArtifactKind,
    ArtifactRecord,
    ArtifactState,
    SourceKind,
    SourceManifest,
    SourceReadiness,
    SourceRecord,
)


def _register_source(
    tmp_path: Path,
    *,
    source_id: str = "video-1",
    include_subtitle: bool = True,
) -> tuple[SourceCatalog, Path]:
    source = SourceRecord(
        source_id=source_id,
        locator=f"https://example.invalid/{source_id}",
        kind=SourceKind.VIDEO,
        registered_at=datetime(2026, 8, 8, 12, 0, tzinfo=UTC),
        title="Example video",
    )
    artifacts = [
        ArtifactRecord(
            artifact_id=f"{source_id}:metadata",
            source_id=source_id,
            kind=ArtifactKind.METADATA,
            relative_path="raw/info.json",
            state=ArtifactState.AVAILABLE,
        )
    ]
    if include_subtitle:
        artifacts.append(
            ArtifactRecord(
                artifact_id=f"{source_id}:subtitle",
                source_id=source_id,
                kind=ArtifactKind.SUBTITLE,
                relative_path="raw/subtitles.en.vtt",
                state=ArtifactState.AVAILABLE,
            )
        )
    catalog = SourceCatalog(tmp_path / "catalog.sqlite3")
    catalog.upsert_manifest(
        SourceManifest(
            source=source,
            artifacts=tuple(artifacts),
            inspected_at=datetime(2026, 8, 8, 12, 1, tzinfo=UTC),
            readiness=(
                SourceReadiness.READY
                if include_subtitle
                else SourceReadiness.PARTIAL
            ),
        )
    )
    artifact_root = tmp_path / "artifacts"
    raw_root = artifact_root / source_id / "raw"
    raw_root.mkdir(parents=True)
    (raw_root / "info.json").write_text(
        json.dumps({"title": "Catalog video", "duration": 30}),
        encoding="utf-8",
    )
    if include_subtitle:
        (raw_root / "subtitles.en.vtt").write_text(
            "WEBVTT\n\n"
            "00:00:00.000 --> 00:00:30.000\n"
            "Wait for a liquidity sweep and market structure shift confirmation.\n",
            encoding="utf-8",
        )
    return catalog, artifact_root


def test_catalog_workflow_persists_and_is_idempotent(tmp_path: Path) -> None:
    catalog, artifact_root = _register_source(tmp_path)
    store = KnowledgeArtifactStore(tmp_path / "knowledge")

    first = process_catalog_source("video-1", catalog, artifact_root, store)
    second = process_catalog_source("video-1", catalog, artifact_root, store)

    assert first["status"] == "processed"
    assert first["quality"]["valid"] is True
    assert second["status"] == "already_current"
    assert (tmp_path / "knowledge/video-1/knowledge.json").is_file()
    assert len(list((tmp_path / "knowledge/video-1/history").glob("*.json"))) == 1


def test_batch_workflow_processes_only_ready_sources(tmp_path: Path) -> None:
    catalog, artifact_root = _register_source(tmp_path)
    _register_source(tmp_path, source_id="video-2", include_subtitle=False)
    store = KnowledgeArtifactStore(tmp_path / "knowledge")

    result = process_ready_sources(catalog, artifact_root, store)

    assert result["ready_source_count"] == 1
    assert result["counts"] == {
        "processed": 1,
        "already_current": 0,
        "blocked": 0,
        "failed": 0,
    }


def test_missing_subtitle_blocks_direct_catalog_processing(tmp_path: Path) -> None:
    catalog, artifact_root = _register_source(
        tmp_path,
        include_subtitle=False,
    )
    store = KnowledgeArtifactStore(tmp_path / "knowledge")

    result = process_catalog_source("video-1", catalog, artifact_root, store)

    assert result["status"] == "blocked"
    assert not (tmp_path / "knowledge/video-1/knowledge.json").exists()


def test_quality_validator_rejects_authority_fields() -> None:
    report = validate_knowledge_artifact(
        {
            "source_id": "video-1",
            "append_only": True,
            "raw_data_modified": False,
            "timeline": {"segments": []},
            "chunks": [],
            "knowledge_units": [],
            "execution_plan": "forbidden",
        }
    )

    assert report.valid is False
    assert any("forbidden authority" in error for error in report.errors)


def test_direct_workflow_preserves_frame_and_ocr_evidence(tmp_path: Path) -> None:
    subtitle = tmp_path / "source.vtt"
    subtitle.write_text(
        "WEBVTT\n\n"
        "00:00:00.000 --> 00:00:10.000\n"
        "Wait for the confirmation.\n",
        encoding="utf-8",
    )

    result = process_source(
        "video-1",
        subtitle,
        frame_index=[{"timestamp": 5, "path": "frames/0005.jpg"}],
        ocr_records=[{"timestamp": 5, "text": "fair value gap"}],
    )

    segment = result["timeline"]["segments"][0]
    assert segment["frame_paths"] == ["frames/0005.jpg"]
    assert segment["ocr_texts"][0]["text"] == "fair value gap"
    assert segment["events"][0]["type"] == "fair_value_gap"
