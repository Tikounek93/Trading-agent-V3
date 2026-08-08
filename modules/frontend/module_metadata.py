"""Release metadata and system_core registration for frontend."""

from modules.system_core.contracts import (
    ContractDeclaration,
    ModuleManifest,
    RuntimeMode,
    SemanticVersion,
)


MODULE_ID = "frontend"
MODULE_VERSION = "0.2.0"
MODULE_STATUS = "candidate"


def build_module_manifest() -> ModuleManifest:
    return ModuleManifest(
        module_id=MODULE_ID,
        version=SemanticVersion.parse(MODULE_VERSION),
        description="Provides the first web surface for source intake operations.",
        supported_modes=frozenset({RuntimeMode.BACKTEST, RuntimeMode.PAPER, RuntimeMode.LIVE}),
        provided_contracts=(
            ContractDeclaration(
                "frontend.source_intake_status",
                SemanticVersion.parse("0.2.0"),
            ),
        ),
    )
