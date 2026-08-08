from datetime import UTC, datetime

import pytest

from modules.system_core.contracts import ModuleStatus, RuntimeMode, SemanticVersion
from modules.system_core.policies import (
    CompatibilityError,
    LiveApproval,
    LifecyclePolicy,
    RuntimeModePolicy,
    assert_compatible,
    require_live_approval,
)
from modules.system_core.tests.test_contracts import _manifest


def test_lifecycle_policy_rejects_unsafe_transition() -> None:
    with pytest.raises(ValueError, match="Cannot transition"):
        LifecyclePolicy().validate(ModuleStatus.REGISTERED, ModuleStatus.READY)


def test_runtime_mode_policy_rejects_unsupported_mode() -> None:
    with pytest.raises(ValueError, match="does not support"):
        RuntimeModePolicy().validate_module(_manifest(), RuntimeMode.LIVE)


def test_live_mode_requires_human_approval() -> None:
    with pytest.raises(PermissionError, match="human approval"):
        require_live_approval(RuntimeMode.LIVE, None)

    require_live_approval(
        RuntimeMode.LIVE,
        LiveApproval(
            approval_id="approval-001",
            approved_by="operator",
            approved_at=datetime(2026, 8, 7, 12, 0, tzinfo=UTC),
        ),
    )


def test_zero_major_contract_requires_exact_version_in_v01() -> None:
    with pytest.raises(CompatibilityError):
        assert_compatible(
            {"sample.output": SemanticVersion.parse("0.1.0")},
            {"sample.output": SemanticVersion.parse("0.2.0")},
        )

    assert_compatible(
        {"sample.output": SemanticVersion.parse("0.1.0")},
        {"sample.output": SemanticVersion.parse("0.1.0")},
    )
