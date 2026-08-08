"""Validation tool for module manifests."""

from ..contracts.module_manifest import ModuleManifest


def validate_module_manifest(manifest: ModuleManifest) -> ModuleManifest:
    if not isinstance(manifest, ModuleManifest):
        raise TypeError("manifest must be ModuleManifest")
    return manifest
