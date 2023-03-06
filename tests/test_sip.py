"""Test SIPs."""
import hashlib
import tarfile

import pytest
from mets_builder import METS, MetsProfile, StructuralMap, StructuralMapDiv

from siptools_ng.sip import SIP
from siptools_ng.sip_digital_object import SIPDigitalObject


def _extract_sip(sip_filepath, extract_filepath):
    """Extract tarred SIP to given path."""
    with tarfile.open(sip_filepath) as sip:
        sip.extractall(extract_filepath)


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


def test_creating_sip_to_existing_filepath(simple_sip):
    """Test that trying to create a SIP to an existing filepath raises
    error.
    """
    with pytest.raises(FileExistsError) as error:
        simple_sip.finalize(
            output_filepath="tests/data/test_file.txt",
            sign_key_filepath="tests/data/rsa-keys.crt"
        )
    assert str(error.value) == (
        "Given output filepath 'tests/data/test_file.txt' exists already."
    )


def test_mets_in_sip(tmp_path, simple_sip):
    """Test that the finalized SIP has a METS file in it."""
    output_filepath = tmp_path / "test_mets_in_sip_output"
    tmp_filepath = tmp_path / "test_mets_in_sip_tmp"
    simple_sip.finalize(
        output_filepath=output_filepath,
        sign_key_filepath="tests/data/rsa-keys.crt",
        tmp_filepath=tmp_filepath
    )

    extract_filepath = tmp_path / "test_mets_in_sip_extracted"
    _extract_sip(output_filepath, extract_filepath)

    mets_filepath = extract_filepath / "mets.xml"
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
    output_filepath = tmp_path / "test_file_location_in_sip_output"
    tmp_filepath = tmp_path / "test_file_location_in_sip_tmp"
    sip.finalize(
        output_filepath=output_filepath,
        sign_key_filepath="tests/data/rsa-keys.crt",
        tmp_filepath=tmp_filepath
    )

    extract_filepath = tmp_path / "test_file_location_in_sip_extracted"
    _extract_sip(output_filepath, extract_filepath)

    assert extract_filepath.is_dir()
    assert (extract_filepath / "data").is_dir()
    assert (extract_filepath / "data" / "files").is_dir()
    assert (extract_filepath / "data" / "files" / "test_file_1.txt").is_file()
    assert (extract_filepath / "data" / "files" / "test_file_2.txt").is_file()


def test_signature_in_sip(tmp_path, simple_sip):
    """Test that the finalized SIP has a signature file with a correct sha sum
    for the METS file in it.
    """
    output_filepath = tmp_path / "test_signature_in_sip_output"
    tmp_filepath = tmp_path / "test_signature_in_sip_tmp"
    simple_sip.finalize(
        output_filepath=output_filepath,
        sign_key_filepath="tests/data/rsa-keys.crt",
        tmp_filepath=tmp_filepath
    )

    extract_filepath = tmp_path / "test_signature_in_sip_extracted"
    _extract_sip(output_filepath, extract_filepath)

    signature_filepath = extract_filepath / "signature.sig"
    assert signature_filepath.is_file()

    mets_filepath = extract_filepath / "mets.xml"
    sha_hash = hashlib.sha1(mets_filepath.read_bytes()).hexdigest()
    assert f"mets.xml:sha1:{sha_hash}" in signature_filepath.read_text("utf-8")


def test_tmp_filepath_for_sip_finalization(tmp_path, simple_sip):
    """Test that user defined temporary path is used for temporary files when
    finalizing SIP.
    """
    output_filepath = (
        tmp_path / "test_mets_filepath_for_sip_finalization_output"
    )
    tmp_filepath = tmp_path / "test_mets_filepath_for_sip_finalization_tmp"

    simple_sip.finalize(
        output_filepath=output_filepath,
        sign_key_filepath="tests/data/rsa-keys.crt",
        tmp_filepath=tmp_filepath
    )
    assert (tmp_filepath / "mets.xml").is_file()
    assert (tmp_filepath / "signature.sig").is_file()


def test_sip_is_tar_file(tmp_path, simple_sip):
    """Test that the finalized SIP is a tar file."""
    output_filepath = tmp_path / "test_sip_is_tar_file_output"
    tmp_filepath = tmp_path / "test_sip_is_tar_file_tmp"
    simple_sip.finalize(
        output_filepath=output_filepath,
        sign_key_filepath="tests/data/rsa-keys.crt",
        tmp_filepath=tmp_filepath
    )
    assert tarfile.is_tarfile(output_filepath)
