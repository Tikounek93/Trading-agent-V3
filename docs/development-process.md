# Development process

The project is developed module by module. A change must leave the module
boundaries, versions and documentation clearer than before the change.

## Standard change sequence

1. Describe the requested behavior and identify the owning module.
2. Prepare a change pack in Agent Atlas.
3. Read the change pack and confirm the allowed context.
4. Inspect only the relevant module, public contracts and reusable tests.
5. Implement the smallest coherent change.
6. Add or update focused reusable tests.
7. Update the module README and the appropriate document in `docs/`.
8. Run the relevant tests and the broader foundation suite when boundaries
   changed.
9. Run Atlas post-change verification.
10. Review the module status and version before calling it stable.

## Agent Atlas

The intended Atlas commands are run from
`/Users/martincerny/Projects/agent-atlas`:

```text
source .venv/bin/activate
python -m atlas.cli prepare-change "<change description>"
python -m atlas.cli post-change-check <change-id>
```

If more context is needed, request an explicit context expansion. Atlas is a
required context and scope tool, not a replacement for code review or tests.

Current limitation: the configured Atlas index still points at the v2
repository. It can prepare and report checks for the v3 work, but its current
post-change result reports no changed files because v3 is outside that index.
Before treating Atlas as a complete v3 gate, v3 must be registered as a first-
class Atlas project or Atlas must be configured with a v3 workspace.

## GitHub

The v3 directory is maintained as a separate local Git repository. Its
`.gitignore` excludes downloaded media, runtime catalogs, staging data, cache
and temporary acquisition files. The v3 repository currently has no configured
Git remote. A GitHub connection should be added after the initial v3 structure
and ownership rules are stable.
The intended workflow is:

- one branch per coherent module change,
- pull request review before merging,
- CI running the reusable test suite and basic static checks,
- no source media or local SQLite runtime data committed to GitHub,
- documentation and module metadata reviewed with the code.

The initial CI workflow is prepared at
`.github/workflows/tests.yml`. The GitHub connector is useful for remote
repositories, pull requests and CI status, but it is not required to define or
implement the local architecture. No GitHub remote is active yet.

## Release gate

A module can move to `stable` only when its declared scope is implemented,
public contracts are explicit, focused tests pass, documentation is current,
and its dependencies report the required readiness. A passing test suite alone
does not make a module stable.
