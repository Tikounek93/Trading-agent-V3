"""Run initialization workflow."""

from datetime import datetime

from ..contracts.run_manifest import RunManifest
from ..contracts.versioning import SemanticVersion
from ..runtime.system_runtime import SystemRuntime


def initialize_run(
    runtime: SystemRuntime,
    run_id: str,
    started_at: datetime,
    strategy_version: SemanticVersion | None = None,
    configuration_version: SemanticVersion | None = None,
) -> RunManifest:
    return runtime.create_run_manifest(
        run_id=run_id,
        started_at=started_at,
        strategy_version=strategy_version,
        configuration_version=configuration_version,
    )
