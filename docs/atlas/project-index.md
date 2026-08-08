# Agent Atlas - Project Index

Repository: `/Users/martincerny/trading_agent_v3`
Detected modules: **8**

## Atlas Maintenance

- Maintenance register: `docs/atlas/maintenance-register.md`
- Documentation inventory: `docs/atlas/documentation-inventory.md`
- Module metadata registry: `docs/atlas/module-metadata.md`
- Module functional spec policy: `docs/atlas/module-functional-spec-policy.md`
- Module functional spec audit: `docs/atlas/module-functional-spec-audit.md`
- Latest module functional spec apply report: `docs/atlas/module-functional-spec-apply.md`

## Atlas Findings

- Findings directory: `docs/atlas/findings/`

## Atlas Contract Runs

- Data contracts overview: `docs/atlas/data-contracts.md`
- Latest contract full run: `docs/atlas/contract-run-report.md`

## Modules

### application

- Confidence: `high`
- Source files: 3
- Test files: 17
- Docs: 0
- Config files: 0

Key source files:
- `modules/__init__.py`
- `scripts/import_v2_source_links.py`
- `scripts/reconcile_artifact_storage.py`

### config

- Confidence: `low`
- Source files: 0
- Test files: 0
- Docs: 0
- Config files: 6

Open questions:
- No tests detected for this module.

### data_platform

- Confidence: `low`
- Source files: 15
- Test files: 0
- Docs: 0
- Config files: 0

Key source files:
- `modules/data_platform/__init__.py`
- `modules/data_platform/catalog/__init__.py`
- `modules/data_platform/catalog/source_catalog.py`
- `modules/data_platform/contracts/__init__.py`
- `modules/data_platform/contracts/storage.py`
- `modules/data_platform/module_metadata.py`
- `modules/data_platform/ports/__init__.py`
- `modules/data_platform/ports/artifact_store.py`
- `modules/data_platform/storage/__init__.py`
- `modules/data_platform/storage/filesystem_artifact_store.py`
- ...and 5 more

Open questions:
- No tests detected for this module.

### documentation

- Confidence: `low`
- Source files: 0
- Test files: 0
- Docs: 15
- Config files: 0

### frontend

- Confidence: `high`
- Source files: 5
- Test files: 1
- Docs: 0
- Config files: 0

Key source files:
- `modules/frontend/__init__.py`
- `modules/frontend/module_metadata.py`
- `modules/frontend/source_intake_app.py`
- `modules/frontend/static/app.js`
- `modules/frontend/tests/__init__.py`

### runtime

- Confidence: `low`
- Source files: 0
- Test files: 1
- Docs: 0
- Config files: 0

Open questions:
- No source files detected for this module.

### source_intake

- Confidence: `low`
- Source files: 27
- Test files: 0
- Docs: 0
- Config files: 0

Key source files:
- `modules/source_intake/__init__.py`
- `modules/source_intake/adapters/__init__.py`
- `modules/source_intake/adapters/youtube_adapter.py`
- `modules/source_intake/agents/__init__.py`
- `modules/source_intake/agents/source_acquisition_agent.py`
- `modules/source_intake/contracts/__init__.py`
- `modules/source_intake/contracts/acquisition.py`
- `modules/source_intake/contracts/artifacts.py`
- `modules/source_intake/contracts/intake.py`
- `modules/source_intake/contracts/source.py`
- ...and 17 more

Open questions:
- No tests detected for this module.

### system_core

- Confidence: `low`
- Source files: 32
- Test files: 0
- Docs: 0
- Config files: 0

Key source files:
- `modules/system_core/__init__.py`
- `modules/system_core/contracts/__init__.py`
- `modules/system_core/contracts/health_status.py`
- `modules/system_core/contracts/lifecycle.py`
- `modules/system_core/contracts/module_manifest.py`
- `modules/system_core/contracts/run_manifest.py`
- `modules/system_core/contracts/runtime_mode.py`
- `modules/system_core/contracts/system_event.py`
- `modules/system_core/contracts/versioning.py`
- `modules/system_core/module_metadata.py`
- ...and 22 more

Open questions:
- No tests detected for this module.
