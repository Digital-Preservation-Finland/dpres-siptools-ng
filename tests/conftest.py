"""Fixtures for tests."""
from pathlib import Path

import pytest
from mets_builder import METS, MetsProfile, StructuralMap, StructuralMapDiv
from packaging import version

from siptools_ng.sip import SIP
from siptools_ng.file import File

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


@pytest.fixture
def simple_mets():
    """A fixture for preparing a simple METS object."""
    return METS(
        mets_profile=MetsProfile.CULTURAL_HERITAGE,
        contract_id="123e4567-e89b-12d3-a456-426614174000",
        creator_name="Mr. Foo",
        creator_type="INDIVIDUAL"
    )


@pytest.fixture
def simple_sip(simple_mets, files):
    """A fixture for preparing a simple SIP object."""
    digital_objects = []
    for file in files:
        digital_objects.append(file.digital_object)
    root_div = StructuralMapDiv("test_div", digital_objects=digital_objects)
    structural_map = StructuralMap(root_div=root_div)
    simple_mets.add_structural_maps([structural_map])
    simple_mets.generate_file_references()
    return SIP.from_files(mets=simple_mets, files=files)


@pytest.fixture
def files():
    """A fixture for preparing a list of digital objects."""
    digital_objects = {
        File(
            path="tests/data/test_file.txt",
            digital_object_path="test_file.txt"
        ),
        File(
            path="tests/data/test_audio.wav",
            digital_object_path="test_audio.wav"
        ),
        File(
            path="tests/data/test_csv.csv",
            digital_object_path="test_csv.csv"
        )
    }

    return digital_objects
