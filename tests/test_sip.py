"""Test SIPs."""
import hashlib
from datetime import datetime

import pytest
from mets_builder import (METS, AgentType, MetsProfile, MetsRecordStatus,
                          StructuralMap, StructuralMapDiv)

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
        sip.finalize(
            output_filepath="sip.tar",
            sign_key_filepath="tests/data/rsa-keys.crt"
        )
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
        sip.finalize(
            output_filepath="tests/data/test_file.txt",
            sign_key_filepath="tests/data/rsa-keys.crt"
        )


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
    sip.finalize(
        output_filepath=output_filepath,
        sign_key_filepath="tests/data/rsa-keys.crt"
    )

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
    sip.finalize(
        output_filepath=output_filepath,
        sign_key_filepath="tests/data/rsa-keys.crt"
    )

    assert output_filepath.is_dir()
    assert (output_filepath / "data").is_dir()
    assert (output_filepath / "data" / "files").is_dir()
    assert (output_filepath / "data" / "files" / "test_file_1.txt").is_file()
    assert (output_filepath / "data" / "files" / "test_file_2.txt").is_file()


def test_signature_in_sip(tmp_path):
    """Test that the finalized SIP has a signature file with a correct sha sum
    for the METS file in it.
    """
    mets = METS(
        mets_profile=MetsProfile.CULTURAL_HERITAGE,
        contract_id="contract_id",
        creator_name="Mr. Foo",
        creator_type=AgentType.INDIVIDUAL,
        package_id="package-id",
        create_date=datetime(2000, 1, 1, 1, 1),
        record_status=MetsRecordStatus.SUBMISSION,
        catalog_version="1.0",
        specification="1.0"
    )
    digital_object = SIPDigitalObject(
        source_filepath="tests/data/test_file.txt",
        sip_filepath="test_file.txt",
        identifier="digital-object-id"
    )
    root_div = StructuralMapDiv("test_div", digital_objects=[digital_object])
    structural_map = StructuralMap(root_div=root_div)
    mets.add_structural_map(structural_map)
    mets.generate_file_references()

    sip = SIP(mets=mets)
    output_filepath = tmp_path / "test_signature_in_sip"
    sip.finalize(
        output_filepath=output_filepath,
        sign_key_filepath="tests/data/rsa-keys.crt"
    )

    signature_filepath = output_filepath / "signature.sig"
    assert signature_filepath.is_file()

    mets_filepath = output_filepath / "mets.xml"
    sha_hash = hashlib.sha1(mets_filepath.read_bytes()).hexdigest()
    assert f"mets.xml:sha1:{sha_hash}" in signature_filepath.read_text("utf-8")
