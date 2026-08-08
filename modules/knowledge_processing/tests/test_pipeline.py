from pathlib import Path

from modules.knowledge_processing.workflows import process_source


def test_source_pipeline_creates_traceable_advisory_knowledge(tmp_path: Path) -> None:
    subtitle = tmp_path / "source.vtt"
    subtitle.write_text(
        "WEBVTT\n\n"
        "00:00:00.000 --> 00:00:12.000\n"
        "Wait for a liquidity sweep and market structure shift confirmation.\n\n"
        "00:00:12.000 --> 00:00:28.000\n"
        "Then use the fair value gap or order block as an entry area.\n",
        encoding="utf-8",
    )

    result = process_source("source-1", subtitle, title="Example")

    assert result["source_id"] == "source-1"
    assert result["append_only"] is True
    assert result["raw_data_modified"] is False
    assert result["timeline"]["segments"][0]["start"] == 0.0
    assert result["chunks"][0]["semantic"]["topics"]
    assert result["knowledge_units"]
    assert {"knowledge_score", "relevance", "score_reasons"} <= set(
        result["knowledge_units"][0]
    )


def test_pipeline_outputs_have_no_strategy_or_execution_authority(
    tmp_path: Path,
) -> None:
    subtitle = tmp_path / "source.vtt"
    subtitle.write_text(
        "WEBVTT\n\n"
        "00:00:00.000 --> 00:00:30.000\n"
        "This is a fair value gap condition and confirmation.\n",
        encoding="utf-8",
    )

    result = process_source("source-2", subtitle)
    output_keys = set(result) | {
        key for unit in result["knowledge_units"] for key in unit
    }
    forbidden = {
        "approve",
        "approved",
        "execute",
        "execution",
        "broker",
        "activate_strategy",
    }

    assert not any(
        any(term in key.lower() for term in forbidden) for key in output_keys
    )
