"""Fixtures for tests."""
from pathlib import Path

import pytest
from mets_builder import METS, MetsProfile, StructuralMap, StructuralMapDiv
from packaging import version

from siptools_ng.sip import SIP
from siptools_ng.sip_digital_object import SIPDigitalObject

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
def simple_sip():
    """A fixture for preparing a simple SIP object."""
    mets = METS(
        mets_profile=MetsProfile.CULTURAL_HERITAGE,
        contract_id="contract_id",
        creator_name="Mr. Foo",
        creator_type="INDIVIDUAL"
    )
    digital_object = SIPDigitalObject(
        source_filepath="tests/data/test_file.txt",
        sip_filepath="test_file.txt"
    )
    root_div = StructuralMapDiv("test_div", digital_objects=[digital_object])
    structural_map = StructuralMap(root_div=root_div)
    mets.add_structural_map(structural_map)
    mets.generate_file_references()

    return SIP(mets=mets)
