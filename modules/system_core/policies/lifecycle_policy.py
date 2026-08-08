"""Policy facade for safe module lifecycle transitions."""

from ..contracts.lifecycle import ModuleStatus, assert_transition


class LifecyclePolicy:
    def validate(self, current: ModuleStatus, target: ModuleStatus) -> None:
        assert_transition(current, target)
