"""Fixtures for tests."""
from pathlib import Path

import pytest
from packaging import version

if version.parse(pytest.__version__) < version.parse("3.9.0"):
    @pytest.fixture(scope="function")
    def tmp_path(tmpdir):
        """A fixture to create a temporary directory used for unit testing
        as a pathlib.Path object.

        This fixture emulates the tmp_path fixture for old pytest
        versions. The fixture is introduced in pytest version
        3.9.0: https://docs.pytest.org/en/6.2.x/tmpdir.html
        """
        return Path(str(tmpdir))
