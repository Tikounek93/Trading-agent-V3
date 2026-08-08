"""Small reusable provider fixture for source_intake acquisition tests."""

from pathlib import Path


class FakeDownloader:
    def __init__(self, options: dict[str, object]) -> None:
        self.options = options

    def __enter__(self) -> "FakeDownloader":
        return self

    def __exit__(self, *_: object) -> None:
        return None

    def extract_info(self, _locator: str, *, download: bool) -> dict[str, object]:
        output_template = str(self.options["outtmpl"])
        if self.options.get("skip_download") is False:
            path = output_template.replace("%(ext)s", "mp4")
            Path(path).write_bytes(b"video")
        elif self.options.get("writesubtitles"):
            raw_dir = Path(output_template).parent
            (raw_dir / "subtitles.en.vtt").write_text("WEBVTT\nen", encoding="utf-8")
            (raw_dir / "subtitles.en-orig.vtt").write_text(
                "WEBVTT\nen-orig",
                encoding="utf-8",
            )
        return {"id": "video_001", "title": "Example"}


def fake_factory(options: dict[str, object]) -> FakeDownloader:
    return FakeDownloader(options)
