from unittest.mock import patch

from nadra.metadata import (
    DISTRIBUTION_NAME,
    FALLBACK_VERSION,
    PACKAGE_NAME,
    project_info,
)


def test_project_info_reports_distribution_package_and_installed_version() -> None:
    with patch("nadra.metadata.version", return_value="1.2.3"):
        info = project_info()

    assert DISTRIBUTION_NAME == "nadra"
    assert PACKAGE_NAME == "nadra"
    assert info.distribution == DISTRIBUTION_NAME
    assert info.package == PACKAGE_NAME
    assert info.version == "1.2.3"


def test_project_info_has_a_source_checkout_fallback() -> None:
    from importlib.metadata import PackageNotFoundError

    with patch("nadra.metadata.version", side_effect=PackageNotFoundError):
        info = project_info()

    assert info.version == FALLBACK_VERSION
