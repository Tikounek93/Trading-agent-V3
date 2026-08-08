"""Release metadata and system_core registration for data_platform."""

from modules.system_core.contracts import (
    ContractDeclaration,
    ModuleManifest,
    RuntimeMode,
    SemanticVersion,
)


MODULE_ID = "data_platform"
MODULE_VERSION = "0.2.0"
MODULE_STATUS = "candidate"


def build_module_manifest() -> ModuleManifest:
    return ModuleManifest(
        module_id=MODULE_ID,
        version=SemanticVersion.parse(MODULE_VERSION),
        description="Stores and reads durable source artifacts through explicit ports.",
        supported_modes=frozenset(
            {RuntimeMode.BACKTEST, RuntimeMode.PAPER, RuntimeMode.LIVE}
        ),
        provided_contracts=(
            ContractDeclaration(
                "data_platform.artifact_store",
                SemanticVersion.parse("0.2.0"),
            ),
            ContractDeclaration(
                "data_platform.stored_artifact",
                SemanticVersion.parse("0.1.0"),
            ),
            ContractDeclaration(
                "data_platform.source_catalog",
                SemanticVersion.parse("0.1.0"),
            ),
        ),
    )
