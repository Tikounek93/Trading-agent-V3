"""Release metadata for knowledge_processing."""

from modules.system_core.contracts import (
    ContractDeclaration,
    ModuleManifest,
    RuntimeMode,
    SemanticVersion,
)


MODULE_ID = "knowledge_processing"
MODULE_VERSION = "1.0.0"
MODULE_STATUS = "stable"


def build_module_manifest() -> ModuleManifest:
    return ModuleManifest(
        module_id=MODULE_ID,
        version=SemanticVersion.parse(MODULE_VERSION),
        description="Transforms source transcripts into structured advisory knowledge artifacts.",
        supported_modes=frozenset(
            {RuntimeMode.BACKTEST, RuntimeMode.PAPER, RuntimeMode.LIVE}
        ),
        provided_contracts=(
            ContractDeclaration(
                "knowledge_processing.timeline",
                SemanticVersion.parse("1.0.0"),
            ),
            ContractDeclaration(
                "knowledge_processing.knowledge_artifact",
                SemanticVersion.parse("1.0.0"),
            ),
        ),
    )
