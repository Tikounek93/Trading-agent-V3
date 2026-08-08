"""Small web application for operating and observing source_intake."""

from __future__ import annotations

import argparse
import json
import threading
from dataclasses import dataclass
from datetime import UTC, datetime
from email.parser import BytesParser
from email.policy import default as email_default_policy
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Callable
from urllib.parse import unquote, urlsplit

from modules.data_platform.catalog import SourceCatalog
from modules.data_platform.storage import FileSystemArtifactStore
from modules.data_platform.workflows import persist_source_manifest
from modules.knowledge_processing.storage import (
    KnowledgeArtifactStore,
    KnowledgeCorrectionStore,
)
from modules.knowledge_processing.workflows import process_catalog_source
from modules.source_intake.contracts import (
    AcquisitionPlan,
    SourceKind,
    SourceRecord,
)
from modules.source_intake.agents import SourceAcquisitionAgent
from modules.source_intake.registry import SourceRegistry
from modules.source_intake.workflows import intake_local_file


DownloaderFactory = Callable[[dict[str, Any]], Any]


@dataclass(frozen=True, slots=True)
class AppConfig:
    intake_root: Path
    durable_root: Path
    catalog_path: Path
    knowledge_root: Path | None = None

    @classmethod
    def from_project_root(cls, project_root: Path) -> "AppConfig":
        root = Path(project_root)
        return cls(
            intake_root=root / "data" / "raw" / "source_intake",
            durable_root=root / "data" / "artifacts",
            catalog_path=root / "data" / "catalog" / "source_catalog.sqlite3",
            knowledge_root=root / "data" / "knowledge",
        )


class SourceIntakeApplication:
    """Application service that composes source_intake and data_platform."""

    def __init__(
        self,
        config: AppConfig,
        downloader_factory: DownloaderFactory | None = None,
    ) -> None:
        self.config = config
        self.registry = SourceRegistry()
        self.agent = SourceAcquisitionAgent(self.registry, downloader_factory)
        self.store = FileSystemArtifactStore(config.durable_root)
        self.catalog = SourceCatalog(config.catalog_path)
        knowledge_root = config.knowledge_root or config.durable_root.parent / "knowledge"
        self.knowledge_store = KnowledgeArtifactStore(knowledge_root)
        self.correction_store = KnowledgeCorrectionStore(knowledge_root)
        self.downloader_factory = downloader_factory
        self._batch_lock = threading.Lock()
        self._batch_status: dict[str, Any] = {
            "running": False,
            "total": 0,
            "completed": 0,
            "failed": 0,
            "current_source_id": None,
            "message": "",
        }
        self._knowledge_lock = threading.Lock()
        self._knowledge_status: dict[str, Any] = {
            "running": False,
            "total": 0,
            "completed": 0,
            "failed": 0,
            "current_source_id": None,
            "message": "",
        }

    def status(self) -> dict[str, Any]:
        sources = self.catalog.list_sources()
        readiness_counts: dict[str, int] = {}
        for source in sources:
            readiness_counts[source.readiness] = readiness_counts.get(source.readiness, 0) + 1
        with self._batch_lock:
            processing = dict(self._batch_status)
        with self._knowledge_lock:
            knowledge_processing = dict(self._knowledge_status)
        return {
            "module": "source_intake",
            "module_version": "1.1.0",
            "module_status": "stable",
            "storage": {
                "durable_root": str(self.config.durable_root),
                "catalog": str(self.config.catalog_path),
            },
            "summary": {
                "source_count": len(sources),
                "readiness": readiness_counts,
            },
            "processing": processing,
            "knowledge_processing": knowledge_processing,
            "knowledge": self.knowledge_status(),
            "sources": [
                {
                    "source_id": source.source_id,
                    "title": source.title or source.source_id,
                    "kind": source.kind,
                    "readiness": source.readiness,
                    "artifact_count": source.artifact_count,
                    "available_artifact_count": source.available_artifact_count,
                    "inspected_at": source.inspected_at.isoformat(),
                    "artifacts": [
                        {
                            "artifact_id": artifact.artifact_id,
                            "kind": artifact.kind,
                            "relative_path": artifact.relative_path,
                            "state": artifact.state,
                            "size_bytes": artifact.size_bytes,
                            "stored_size_bytes": artifact.stored_size_bytes,
                            "sha256": artifact.sha256,
                        }
                        for artifact in self.catalog.list_artifacts(source.source_id)
                    ],
                }
                for source in sources
            ],
        }

    def knowledge_status(self) -> dict[str, Any]:
        summaries = self.catalog.list_sources()
        sources = []
        for source in summaries:
            available = self.knowledge_store.exists(source.source_id)
            artifact_summary: dict[str, Any] = {
                "knowledge_available": available,
                "correction_count": self.correction_store.count(source.source_id),
            }
            if available:
                artifact = self.knowledge_store.load(source.source_id)
                artifact_summary.update(
                    {
                        "pipeline_version": artifact.get("pipeline_version"),
                        "chunks_count": len(artifact.get("chunks", [])),
                        "units_count": artifact.get("units_count", len(artifact.get("knowledge_units", []))),
                        "title": artifact.get("timeline", {}).get("title"),
                    }
                )
            sources.append(
                {
                    "source_id": source.source_id,
                    "title": source.title or source.source_id,
                    "readiness": source.readiness,
                    **artifact_summary,
                }
            )
        with self._knowledge_lock:
            processing = dict(self._knowledge_status)
        return {
            "module": "knowledge_processing",
            "module_version": "1.0.0",
            "module_status": "stable",
            "summary": {
                "catalog_sources": len(summaries),
                "processed_sources": sum(
                    1 for source in sources if source["knowledge_available"]
                ),
                "corrections": sum(source["correction_count"] for source in sources),
            },
            "processing": processing,
            "sources": sources,
        }

    def get_knowledge(self, source_id: str) -> dict[str, Any]:
        artifact = self.knowledge_store.load(source_id)
        return {
            "source_id": source_id,
            "artifact": artifact,
            "corrections": self.correction_store.list(source_id),
        }

    def create_knowledge_correction(
        self,
        source_id: str,
        payload: dict[str, Any],
    ) -> dict[str, Any]:
        correction = self.correction_store.create(
            source_id,
            target_type=str(payload.get("target_type", "")),
            target_id=str(payload.get("target_id", "")),
            field=str(payload.get("field", "")),
            corrected_value=payload.get("corrected_value"),
            reason=str(payload.get("reason", "")),
            author=str(payload.get("author") or "operator"),
        )
        return {
            "correction": correction,
            "knowledge": self.get_knowledge(source_id),
        }

    def start_knowledge_processing(self, source_id: str | None = None) -> dict[str, Any]:
        if source_id:
            source_ids = (source_id,)
        else:
            source_ids = tuple(
                source.source_id
                for source in self.catalog.list_sources()
                if source.readiness == "ready"
            )
        with self._knowledge_lock:
            if self._knowledge_status["running"]:
                return dict(self._knowledge_status)
            if not source_ids:
                self._knowledge_status = {
                    "running": False,
                    "total": 0,
                    "completed": 0,
                    "failed": 0,
                    "current_source_id": None,
                    "message": "No ready knowledge sources",
                }
                return dict(self._knowledge_status)
            self._knowledge_status = {
                "running": True,
                "total": len(source_ids),
                "completed": 0,
                "failed": 0,
                "current_source_id": None,
                "message": "Knowledge processing started",
            }
        threading.Thread(
            target=self._run_knowledge_processing,
            args=(source_ids,),
            daemon=True,
            name="knowledge-processing-batch",
        ).start()
        return dict(self._knowledge_status)

    def _run_knowledge_processing(self, source_ids: tuple[str, ...]) -> None:
        for source_id in source_ids:
            with self._knowledge_lock:
                self._knowledge_status["current_source_id"] = source_id
                self._knowledge_status["message"] = f"Processing {source_id}"
            try:
                result = process_catalog_source(
                    source_id,
                    self.catalog,
                    self.config.durable_root,
                    self.knowledge_store,
                )
                with self._knowledge_lock:
                    self._knowledge_status["completed"] += 1
                    if result.get("status") in {"failed", "blocked"}:
                        self._knowledge_status["failed"] += 1
                    self._knowledge_status["message"] = (
                        f"{result.get('status', 'unknown')}: {source_id}"
                    )
            except Exception as exc:
                with self._knowledge_lock:
                    self._knowledge_status["completed"] += 1
                    self._knowledge_status["failed"] += 1
                    self._knowledge_status["message"] = f"Failed {source_id}: {exc}"
        with self._knowledge_lock:
            self._knowledge_status["running"] = False
            self._knowledge_status["current_source_id"] = None
            self._knowledge_status["message"] = "Knowledge processing finished"

    def acquire(self, payload: dict[str, Any]) -> dict[str, Any]:
        source_id = payload.get("source_id", "")
        locator = payload.get("locator", "")
        title = payload.get("title") or None
        kind = SourceKind(payload.get("kind", SourceKind.VIDEO.value))
        plan = AcquisitionPlan(
            download_video=bool(payload.get("download_video", False)),
            fetch_metadata=bool(payload.get("fetch_metadata", False)),
            fetch_subtitles=bool(payload.get("fetch_subtitles", False)),
        )
        source = SourceRecord(
            source_id=source_id,
            locator=locator,
            kind=kind,
            title=title,
            registered_at=datetime.now(UTC),
        )
        result = self.agent.run(
            source=source,
            artifact_root=self.config.intake_root / source.source_id,
            plan=plan,
            inspected_at=datetime.now(UTC),
        )
        persistence = persist_source_manifest(
            manifest=result.intake_result.manifest,
            artifact_root=self.config.intake_root / source.source_id,
            store=self.store,
            catalog=self.catalog,
        )
        return {
            "source_id": source.source_id,
            "readiness": result.intake_result.manifest.readiness.value,
            "acquisitions": [
                {
                    "operation": item.operation,
                    "status": item.status.value,
                    "message": item.message,
                }
                for item in result.acquisitions
            ],
            "stored_artifact_count": len(persistence.stored_artifacts),
            "status": self.status(),
        }

    def upload_local(
        self,
        payload: dict[str, Any],
        filename: str,
        content: bytes,
    ) -> dict[str, Any]:
        kind = SourceKind(payload.get("kind", SourceKind.DOCUMENT.value))
        source = SourceRecord(
            source_id=payload.get("source_id", ""),
            locator=f"local://{Path(filename).name}",
            kind=kind,
            title=payload.get("title") or filename,
            registered_at=datetime.now(UTC),
        )
        artifact_root = self.config.intake_root / source.source_id
        result = intake_local_file(
            registry=self.registry,
            source=source,
            artifact_root=artifact_root,
            filename=filename,
            content=content,
            inspected_at=datetime.now(UTC),
        )
        persistence = persist_source_manifest(
            manifest=result.intake_result.manifest,
            artifact_root=artifact_root,
            store=self.store,
            catalog=self.catalog,
        )
        return {
            "source_id": source.source_id,
            "readiness": result.intake_result.manifest.readiness.value,
            "stored_artifact_count": len(persistence.stored_artifacts),
            "status": self.status(),
        }

    def start_batch_processing(self) -> dict[str, Any]:
        sources = tuple(
            source
            for source in self.catalog.list_source_records()
            if self._source_readiness(source.source_id) != "ready"
        )
        with self._batch_lock:
            if self._batch_status["running"]:
                return dict(self._batch_status)
            if not sources:
                self._batch_status = {
                    "running": False,
                    "total": 0,
                    "completed": 0,
                    "failed": 0,
                    "current_source_id": None,
                    "message": "No pending sources",
                }
                return dict(self._batch_status)
            self._batch_status = {
                "running": True,
                "total": len(sources),
                "completed": 0,
                "failed": 0,
                "current_source_id": None,
                "message": "Batch processing started",
            }
        threading.Thread(
            target=self._run_batch_processing,
            args=(sources,),
            daemon=True,
            name="source-intake-batch",
        ).start()
        return self.status()["processing"]

    def _source_readiness(self, source_id: str) -> str:
        return next(
            (source.readiness for source in self.catalog.list_sources() if source.source_id == source_id),
            "not_ready",
        )

    def _run_batch_processing(self, sources: tuple[SourceRecord, ...]) -> None:
        plan = AcquisitionPlan(
            download_video=True,
            fetch_metadata=True,
            fetch_subtitles=True,
        )
        for source in sources:
            with self._batch_lock:
                self._batch_status["current_source_id"] = source.source_id
                self._batch_status["message"] = f"Processing {source.source_id}"
            try:
                artifact_root = self.config.intake_root / source.source_id
                result = self.agent.run(
                    source=source,
                    artifact_root=artifact_root,
                    plan=plan,
                    inspected_at=datetime.now(UTC),
                )
                persistence = persist_source_manifest(
                    manifest=result.intake_result.manifest,
                    artifact_root=artifact_root,
                    store=self.store,
                    catalog=self.catalog,
                )
                failed = any(item.status.value != "prepared" for item in result.acquisitions)
                with self._batch_lock:
                    self._batch_status["completed"] += 1
                    if failed:
                        self._batch_status["failed"] += 1
                    self._batch_status["message"] = (
                        f"Completed {source.source_id}; "
                        f"stored {len(persistence.stored_artifacts)} artifacts"
                    )
            except Exception as exc:
                with self._batch_lock:
                    self._batch_status["completed"] += 1
                    self._batch_status["failed"] += 1
                    self._batch_status["message"] = f"Failed {source.source_id}: {exc}"
        with self._batch_lock:
            self._batch_status["running"] = False
            self._batch_status["current_source_id"] = None
            self._batch_status["message"] = "Batch processing finished"


def _json_bytes(payload: Any) -> bytes:
    return json.dumps(payload, ensure_ascii=True).encode("utf-8")


def _parse_multipart_form(
    body: bytes,
    content_type: str,
) -> tuple[dict[str, str], dict[str, tuple[str, bytes]]]:
    """Parse the small multipart form used by the local-file endpoint."""

    header = (
        f"Content-Type: {content_type}\r\n"
        "MIME-Version: 1.0\r\n\r\n"
    ).encode("utf-8")
    message = BytesParser(policy=email_default_policy).parsebytes(header + body)
    fields: dict[str, str] = {}
    files: dict[str, tuple[str, bytes]] = {}
    for part in message.iter_parts():
        name = part.get_param("name", header="content-disposition")
        if not name:
            continue
        filename = part.get_filename()
        content = part.get_payload(decode=True) or b""
        if filename is not None:
            files[name] = (filename, content)
        else:
            fields[name] = content.decode("utf-8")
    return fields, files


def create_server(
    application: SourceIntakeApplication,
    host: str = "127.0.0.1",
    port: int = 8765,
) -> ThreadingHTTPServer:
    static_root = Path(__file__).parent / "static"

    class Handler(BaseHTTPRequestHandler):
        def _send_json(self, payload: Any, status: HTTPStatus = HTTPStatus.OK) -> None:
            body = _json_bytes(payload)
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def _send_file(self, path: Path, content_type: str) -> None:
            if not path.is_file():
                self._send_json({"error": "not found"}, HTTPStatus.NOT_FOUND)
                return
            body = path.read_bytes()
            self.send_response(HTTPStatus.OK)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def do_GET(self) -> None:  # noqa: N802
            path = urlsplit(self.path).path
            if path == "/api/status":
                self._send_json(application.status())
                return
            if path == "/api/knowledge/status":
                self._send_json(application.knowledge_status())
                return
            if path.startswith("/api/knowledge/"):
                source_id = unquote(path.removeprefix("/api/knowledge/")).strip("/")
                if source_id and "/" not in source_id:
                    try:
                        self._send_json(application.get_knowledge(source_id))
                    except FileNotFoundError:
                        self._send_json({"error": "knowledge artifact not found"}, HTTPStatus.NOT_FOUND)
                    except ValueError as exc:
                        self._send_json({"error": str(exc)}, HTTPStatus.BAD_REQUEST)
                    return
            if path == "/":
                self._send_file(static_root / "index.html", "text/html; charset=utf-8")
                return
            if path == "/static/app.js":
                self._send_file(static_root / "app.js", "text/javascript; charset=utf-8")
                return
            if path == "/static/styles.css":
                self._send_file(static_root / "styles.css", "text/css; charset=utf-8")
                return
            self._send_json({"error": "not found"}, HTTPStatus.NOT_FOUND)

        def do_POST(self) -> None:  # noqa: N802
            path = urlsplit(self.path).path
            if path == "/api/knowledge/process":
                try:
                    length = int(self.headers.get("Content-Length", "0"))
                    if length > 64 * 1024:
                        raise ValueError("request is too large")
                    payload = json.loads(self.rfile.read(length).decode("utf-8") or "{}")
                    if not isinstance(payload, dict):
                        raise ValueError("request body must be an object")
                    self._send_json(
                        application.start_knowledge_processing(payload.get("source_id")),
                        HTTPStatus.ACCEPTED,
                    )
                except (ValueError, KeyError, json.JSONDecodeError) as exc:
                    self._send_json({"error": str(exc)}, HTTPStatus.BAD_REQUEST)
                return
            if path.startswith("/api/knowledge/") and path.endswith("/corrections"):
                source_id = unquote(path.removeprefix("/api/knowledge/").removesuffix("/corrections")).strip("/")
                try:
                    length = int(self.headers.get("Content-Length", "0"))
                    if length > 128 * 1024:
                        raise ValueError("request is too large")
                    payload = json.loads(self.rfile.read(length).decode("utf-8"))
                    if not isinstance(payload, dict):
                        raise ValueError("request body must be an object")
                    self._send_json(
                        application.create_knowledge_correction(source_id, payload),
                        HTTPStatus.CREATED,
                    )
                except (ValueError, KeyError, json.JSONDecodeError) as exc:
                    self._send_json({"error": str(exc)}, HTTPStatus.BAD_REQUEST)
                except FileNotFoundError:
                    self._send_json({"error": "knowledge artifact not found"}, HTTPStatus.NOT_FOUND)
                return
            if path == "/api/source-intake/upload":
                try:
                    length = int(self.headers.get("Content-Length", "0"))
                    if length > 512 * 1024 * 1024:
                        raise ValueError("upload is too large")
                    fields, files = _parse_multipart_form(
                        self.rfile.read(length),
                        self.headers.get("Content-Type", ""),
                    )
                    if "file" not in files:
                        raise ValueError("a local file is required")
                    filename, content = files["file"]
                    payload = {
                        "source_id": fields.get("source_id", ""),
                        "title": fields.get("title", ""),
                        "kind": fields.get("kind", SourceKind.DOCUMENT.value),
                    }
                    self._send_json(
                        application.upload_local(
                            payload,
                            filename,
                            content,
                        ),
                        HTTPStatus.CREATED,
                    )
                except (ValueError, KeyError) as exc:
                    self._send_json({"error": str(exc)}, HTTPStatus.BAD_REQUEST)
                except Exception as exc:
                    self._send_json({"error": str(exc)}, HTTPStatus.INTERNAL_SERVER_ERROR)
                return
            if path == "/api/source-intake/process-all":
                self._send_json(application.start_batch_processing(), HTTPStatus.ACCEPTED)
                return
            if path != "/api/source-intake/acquire":
                self._send_json({"error": "not found"}, HTTPStatus.NOT_FOUND)
                return
            try:
                length = int(self.headers.get("Content-Length", "0"))
                if length > 64 * 1024:
                    raise ValueError("request is too large")
                payload = json.loads(self.rfile.read(length).decode("utf-8"))
                if not isinstance(payload, dict):
                    raise ValueError("request body must be an object")
                self._send_json(application.acquire(payload), HTTPStatus.CREATED)
            except (ValueError, KeyError) as exc:
                self._send_json({"error": str(exc)}, HTTPStatus.BAD_REQUEST)
            except Exception as exc:  # provider failures are returned as an operator error
                self._send_json({"error": str(exc)}, HTTPStatus.INTERNAL_SERVER_ERROR)

        def log_message(self, format: str, *args: Any) -> None:
            return

    return ThreadingHTTPServer((host, port), Handler)


def run_server(config: AppConfig, host: str = "127.0.0.1", port: int = 8765) -> None:
    server = create_server(SourceIntakeApplication(config), host=host, port=port)
    print(f"source_intake web app: http://{host}:{server.server_port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the source intake web app")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument(
        "--project-root",
        type=Path,
        default=Path(__file__).resolve().parents[2],
    )
    args = parser.parse_args()
    run_server(AppConfig.from_project_root(args.project_root), args.host, args.port)


if __name__ == "__main__":
    main()
