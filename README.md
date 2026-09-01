# Nadra

Nadra is a secure, AI-driven automation architecture that integrates specialized agents for data
processing, real-time monitoring, and content creation while implementing rigorous,
security-by-design protocols to mitigate cyber threats.

The repository currently provides the typed Python package, command-line identity seam,
reproducible development environment, quality gates, and specification-driven delivery workflow.
The full domain design will be added later. Agent orchestration, monitoring, content workflows, and
security controls are therefore product direction, not claims about behavior already implemented.

## Quick start

Requirements: Git, Make, and [uv](https://docs.astral.sh/uv/).

```bash
git clone https://github.com/volod/nadra.git
cd nadra
make bootstrap
make doctor
make run
make ci
```

`make bootstrap` creates `.venv` from the committed lockfile. `make run` executes `nadra info`,
which reports the installed distribution, version, and import package. `make ci` runs the same
required checks as GitHub Actions.

## Current foundation

- Python 3.12+ package under `src/nadra/` with a typed public identity API.
- Installed `nadra` CLI and `nadra-plan` planning-status command.
- Locked dependency management through `uv`, `uv.lock`, and Make workflows.
- Deterministic tests plus formatting, linting, typing, coverage, complexity, shell, and
  documentation checks.
- One canonical agent policy in `AGENTS.md`, with thin adapters for supported coding tools.
- A living product specification, forward-only plan, and current-state documentation tree.

The package identity can also be inspected from Python:

```python
from nadra import project_info

print(project_info())
```

## Development commands

| Command | Purpose |
| --- | --- |
| `make help` | List supported workflows |
| `make bootstrap` | Create or update the locked development environment |
| `make doctor` | Verify tools, repository files, and the installed package |
| `make run` | Run `nadra info` |
| `make test` | Run the deterministic unit test suite |
| `make coverage` | Run tests with the coverage gate |
| `make format` | Apply Ruff formatting |
| `make ci` | Run required local and CI checks |
| `make quality` | Run CI checks, coverage, Markdown lint, and package build |
| `make plan-status` | Count tasks and show the next agent and human work |
| `make lint-spec-plan` | Check the capability registry against the plan |
| `make lint-doc-links` | Check relative Markdown files and anchors |
| `make quality-report` | Report files over the soft size limit |

Use Make targets for repeatable workflows. Before a direct `uv` command, source
`scripts/shared/common.sh` and run `nadra_load_env` so cache and link behavior follows `.env`.

## Documentation model

```text
docs/design/spec.md        what Nadra must do and how each capability is evaluated
          |
          v
docs/impl/plan.md          only work that remains, ordered by capability
          |
          v
docs/impl/current.md       index of behavior that exists now
```

The specification is living. A newly defined product capability starts in the specification with
its boundary and evaluation, enters the forward plan, and moves to current-state documentation
when available. See the [planning workflow](docs/guides/planning-workflow.md) and
[development guide](docs/guides/development.md).

## Agent support

`AGENTS.md` is the canonical policy. `CLAUDE.md`, `GEMINI.md`, `.codex`, and the Cursor rule are
thin adapters that point to it, keeping repository instructions consistent across tools.

## Layout

```text
src/nadra/                 production package and repository quality tooling
tests/                     unit and governance tests
docs/design/               product specification
docs/impl/plan.md          forward-only work
docs/impl/current/         delivered behavior
docs/guides/               contributor workflows
scripts/shared/            shared shell environment helpers
.github/workflows/         required CI
```

Runtime output belongs under `$DATA_DIR/<method>/<run-id>/`. It defaults to `.data/` and is ignored
by Git.

## License

MIT. See [LICENSE](LICENSE).
