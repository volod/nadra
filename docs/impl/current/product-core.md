# Product Core

The `nadra` package provides a typed `ProjectInfo` value through `project_info()`. It
reports the distribution name, import package, and installed version, with a source-checkout
fallback when distribution metadata is unavailable.

`src/nadra/cli.py` owns argument parsing. The installed `nadra info` command logs the same
identity, providing a packaging and executable-path smoke test without choosing a business-domain
framework.

`pyproject.toml` declares the `nadra` distribution, the `nadra` and `nadra-plan` console scripts,
and the project repository and documentation URLs. Mypy and coverage target the `src/nadra/`
package, while `uv.lock` records the same distribution identity.

Run it with:

```bash
make run
```

`tests/test_metadata.py` and `tests/test_cli.py` cover the API, package constants, parser identity,
and command boundary. `make doctor`, `make run`, and `make ci` verify the installed import, CLI, and
repository gates. `make build` produces `nadra` source and wheel distributions.
