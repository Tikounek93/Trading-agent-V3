"""Release metadata and system_core registration for source_intake."""

from modules.system_core.contracts import (
    ContractDeclaration,
    ModuleManifest,
    RuntimeMode,
    SemanticVersion,
)


MODULE_ID = "source_intake"
MODULE_VERSION = "1.1.0"
MODULE_STATUS = "stable"


def build_module_manifest() -> ModuleManifest:
    """Return the source_intake manifest consumed by system_core."""

    return ModuleManifest(
        module_id=MODULE_ID,
        version=SemanticVersion.parse(MODULE_VERSION),
        description="Registers, acquires and describes knowledge source artifacts.",
        supported_modes=frozenset(
            {RuntimeMode.BACKTEST, RuntimeMode.PAPER, RuntimeMode.LIVE}
        ),
        provided_contracts=(
            ContractDeclaration(
                "source_intake.source_record",
                SemanticVersion.parse("0.1.0"),
            ),
            ContractDeclaration(
                "source_intake.artifact_manifest",
                SemanticVersion.parse("0.1.0"),
            ),
            ContractDeclaration(
                "source_intake.acquisition_result",
                SemanticVersion.parse("0.1.0"),
            ),
            ContractDeclaration(
                "source_intake.source_manifest",
                SemanticVersion.parse("1.0.0"),
            ),
            ContractDeclaration(
                "source_intake.local_file_result",
                SemanticVersion.parse("0.1.0"),
            ),
        ),
    )
