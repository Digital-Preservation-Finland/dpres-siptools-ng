"""Test SIPs."""
import pytest
from mets_builder import METS, MetsProfile, StructuralMap, StructuralMapDiv

from siptools_ng.sip import SIP
from siptools_ng.sip_digital_object import SIPDigitalObject


def test_creating_sip_with_zero_files():
    """Test that creating a SIP with zero files results in error."""
    mets = METS(
        mets_profile=MetsProfile.CULTURAL_HERITAGE,
        contract_id="contract_id",
        creator_name="Mr. Foo"
    )
    sip = SIP(mets=mets)

    with pytest.raises(ValueError) as error:
        sip.finalize(output_filepath="sip.tar")
    assert str(error.value) == "SIP does not contain any digital objects."


def test_creating_sip_to_existing_filepath():
    """Test that trying to create a SIP to an existing filepath raises
    error.
    """
    mets = METS(
        mets_profile=MetsProfile.CULTURAL_HERITAGE,
        contract_id="contract_id",
        creator_name="Mr. Foo"
    )
    digital_object = SIPDigitalObject(
        source_filepath="tests/data/test_file.txt",
        sip_filepath="test_file.txt"
    )
    root_div = StructuralMapDiv("test_div", digital_objects=[digital_object])
    structural_map = StructuralMap(root_div=root_div)
    mets.add_structural_map(structural_map)
    mets.generate_file_references()
    sip = SIP(mets=mets)

    with pytest.raises(FileExistsError):
        sip.finalize(output_filepath="tests/data/test_file.txt")


def test_mets_in_sip(tmp_path):
    """Test that the finalized SIP has a METS file in it."""
    mets = METS(
        mets_profile=MetsProfile.CULTURAL_HERITAGE,
        contract_id="contract_id",
        creator_name="Mr. Foo"
    )
    digital_object = SIPDigitalObject(
        source_filepath="tests/data/test_file.txt",
        sip_filepath="test_file.txt"
    )
    root_div = StructuralMapDiv("test_div", digital_objects=[digital_object])
    structural_map = StructuralMap(root_div=root_div)
    mets.add_structural_map(structural_map)
    mets.generate_file_references()

    sip = SIP(mets=mets)
    output_filepath = tmp_path / "test_mets_in_sip"
    sip.finalize(output_filepath=output_filepath)

    mets_filepath = output_filepath / "mets.xml"
    assert mets_filepath.exists()

    mets_contents = mets_filepath.read_text()
    assert mets_contents.startswith("<mets:mets")


def test_file_location_in_sip(tmp_path):
    """Test that digital objects are copied to the right path in the finalized
    SIP.
    """
    mets = METS(
        mets_profile=MetsProfile.CULTURAL_HERITAGE,
        contract_id="contract_id",
        creator_name="Mr. Foo"
    )
    digital_object_1 = SIPDigitalObject(
        source_filepath="tests/data/test_file.txt",
        sip_filepath="data/files/test_file_1.txt"
    )
    digital_object_2 = SIPDigitalObject(
        source_filepath="tests/data/test_file.txt",
        sip_filepath="data/files/test_file_2.txt"
    )
    digital_objects = [digital_object_1, digital_object_2]
    root_div = StructuralMapDiv("test_div", digital_objects=digital_objects)
    structural_map = StructuralMap(root_div=root_div)
    mets.add_structural_map(structural_map)
    mets.generate_file_references()

    sip = SIP(mets=mets)
    output_filepath = tmp_path / "test_file_location_in_sip"
    sip.finalize(output_filepath=output_filepath)

    assert output_filepath.is_dir()
    assert (output_filepath / "data").is_dir()
    assert (output_filepath / "data" / "files").is_dir()
    assert (output_filepath / "data" / "files" / "test_file_1.txt").is_file()
    assert (output_filepath / "data" / "files" / "test_file_2.txt").is_file()
