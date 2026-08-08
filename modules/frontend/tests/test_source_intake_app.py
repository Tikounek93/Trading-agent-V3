import json
import threading
import time
from datetime import UTC, datetime
import urllib.request

from modules.frontend.source_intake_app import (
    AppConfig,
    SourceIntakeApplication,
    create_server,
)
from modules.source_intake.tests.fixtures import fake_factory
from modules.data_platform.workflows import register_source_links
from modules.frontend.source_intake_app import _parse_multipart_form
from modules.knowledge_processing.storage import KnowledgeArtifactStore


def test_source_intake_app_exposes_status_and_acquisition_api(tmp_path) -> None:
    application = SourceIntakeApplication(
        AppConfig(
            intake_root=tmp_path / "intake",
            durable_root=tmp_path / "durable",
            catalog_path=tmp_path / "catalog.sqlite3",
        ),
        downloader_factory=fake_factory,
    )
    server = create_server(application, port=0)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    base_url = f"http://127.0.0.1:{server.server_port}"
    try:
        with urllib.request.urlopen(f"{base_url}/api/status") as response:
            initial = json.load(response)
        assert initial["summary"]["source_count"] == 0

        request = urllib.request.Request(
            f"{base_url}/api/source-intake/acquire",
            data=json.dumps(
                {
                    "source_id": "video_001",
                    "locator": "https://example.invalid/video_001",
                    "kind": "video",
                    "download_video": True,
                    "fetch_metadata": True,
                    "fetch_subtitles": True,
                }
            ).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(request) as response:
            result = json.load(response)
        assert result["stored_artifact_count"] == 4
        assert result["status"]["summary"]["source_count"] == 1
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)


def test_source_intake_app_starts_batch_processing(tmp_path) -> None:
    application = SourceIntakeApplication(
        AppConfig(
            intake_root=tmp_path / "intake",
            durable_root=tmp_path / "durable",
            catalog_path=tmp_path / "catalog.sqlite3",
        ),
        downloader_factory=fake_factory,
    )
    register_source_links(
        application.registry,
        application.catalog,
        ("https://www.youtube.com/watch?v=abc_DEF12345",),
        datetime(2026, 8, 8, tzinfo=UTC),
    )

    started = application.start_batch_processing()
    assert started["running"] is True
    for _ in range(30):
        if not application.status()["processing"]["running"]:
            break
        time.sleep(0.02)

    processing = application.status()["processing"]
    assert processing["completed"] == 1
    assert processing["failed"] == 0


def test_source_intake_app_accepts_local_document(tmp_path) -> None:
    application = SourceIntakeApplication(
        AppConfig(
            intake_root=tmp_path / "intake",
            durable_root=tmp_path / "durable",
            catalog_path=tmp_path / "catalog.sqlite3",
        )
    )

    result = application.upload_local(
        {"source_id": "document_001", "kind": "document", "title": "Lesson"},
        "lesson.pdf",
        b"local document",
    )

    assert result["stored_artifact_count"] == 1
    assert result["status"]["sources"][0]["kind"] == "document"


def test_multipart_local_file_form_parser_keeps_fields_and_bytes() -> None:
    boundary = "TestBoundary"
    body = (
        f"--{boundary}\r\nContent-Disposition: form-data; name=source_id\r\n\r\ndoc_001\r\n"
        f"--{boundary}\r\nContent-Disposition: form-data; name=kind\r\n\r\ndocument\r\n"
        f"--{boundary}\r\nContent-Disposition: form-data; name=file; filename=lesson.pdf\r\n"
        "Content-Type: application/pdf\r\n\r\n"
    ).encode("utf-8") + b"PDF bytes\r\n" + f"--{boundary}--\r\n".encode("utf-8")

    fields, files = _parse_multipart_form(body, f"multipart/form-data; boundary={boundary}")

    assert fields == {"source_id": "doc_001", "kind": "document"}
    assert files["file"] == ("lesson.pdf", b"PDF bytes")


def test_frontend_exposes_knowledge_status_and_append_only_correction(tmp_path) -> None:
    application = SourceIntakeApplication(
        AppConfig(
            intake_root=tmp_path / "intake",
            durable_root=tmp_path / "durable",
            catalog_path=tmp_path / "catalog.sqlite3",
            knowledge_root=tmp_path / "knowledge",
        )
    )
    KnowledgeArtifactStore(tmp_path / "knowledge").save(
        "video_001",
        {
            "source_id": "video_001",
            "pipeline_version": "1.0.0",
            "append_only": True,
            "raw_data_modified": False,
            "timeline": {"title": "Example", "segments": []},
            "chunks": [],
            "knowledge_units": [],
            "units_count": 0,
        },
    )

    status = application.knowledge_status()
    assert status["module_version"] == "1.0.0"
    assert status["summary"]["processed_sources"] == 0

    correction_store = application.correction_store
    correction = correction_store.create(
        "video_001",
        target_type="knowledge_unit",
        target_id="unit_001",
        field="note",
        corrected_value="Review",
        reason="Operator review note",
    )
    assert correction["append_only"] is True
    assert application.get_knowledge("video_001")["corrections"][0]["field"] == "note"
