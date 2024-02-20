"""Test SIPs."""
import hashlib
import tarfile

import pytest
from mets_builder import METS, MetsProfile
from mets_builder.metadata import DigitalProvenanceEventMetadata

from siptools_ng import digital_provenance
from siptools_ng.sip import SIP


def _extract_sip(sip_filepath, extract_filepath):
    """Extract tarred SIP to given path."""
    with tarfile.open(sip_filepath) as sip:
        sip.extractall(extract_filepath)


def _get_testing_filepaths(tmp_path_of_test):
    """Get filepaths for directing files produced by the tests to a canonized
    location.
    """
    output_filepath = tmp_path_of_test / "finalized_sip.tar"
    extracted_filepath = tmp_path_of_test / "extracted_sip"
    return output_filepath, extracted_filepath


def test_creating_sip_with_zero_files():
    """Test that creating a SIP with zero files results in error."""
    mets = METS(
        mets_profile=MetsProfile.CULTURAL_HERITAGE,
        contract_id="contract_id",
        creator_name="Mr. Foo",
        creator_type="INDIVIDUAL"
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
    output_filepath, extracted_filepath = _get_testing_filepaths(tmp_path)

    simple_sip.finalize(
        output_filepath=output_filepath,
        sign_key_filepath="tests/data/rsa-keys.crt"
    )

    _extract_sip(output_filepath, extracted_filepath)

    mets_filepath = extracted_filepath / "mets.xml"
    assert mets_filepath.exists()

    mets_contents = mets_filepath.read_text()
    assert mets_contents.startswith("<mets:mets")


def test_signature_in_sip(tmp_path, simple_sip):
    """Test that the finalized SIP has a signature file with a correct sha sum
    for the METS file in it.
    """
    output_filepath, extracted_filepath = _get_testing_filepaths(tmp_path)

    simple_sip.finalize(
        output_filepath=output_filepath,
        sign_key_filepath="tests/data/rsa-keys.crt"
    )

    _extract_sip(output_filepath, extracted_filepath)

    signature_filepath = extracted_filepath / "signature.sig"
    assert signature_filepath.is_file()

    mets_filepath = extracted_filepath / "mets.xml"
    sha_hash = hashlib.sha1(mets_filepath.read_bytes()).hexdigest()
    assert f"mets.xml:sha1:{sha_hash}" in signature_filepath.read_text("utf-8")


def test_sip_is_tar_file(tmp_path, simple_sip):
    """Test that the finalized SIP is a tar file."""
    output_filepath, _ = _get_testing_filepaths(tmp_path)

    simple_sip.finalize(
        output_filepath=output_filepath,
        sign_key_filepath="tests/data/rsa-keys.crt"
    )
    assert tarfile.is_tarfile(output_filepath)


@pytest.mark.parametrize(
    ("filepath", "error_message"),
    (
        (
            "nonexistent_filepath",
            "Path 'nonexistent_filepath' does not exist."
        ),
        (
            "tests/data/test_file.txt",
            "Path 'tests/data/test_file.txt' is not a directory."
        )
    )
)
def test_generating_sip_from_invalid_filepath(
    filepath, error_message, simple_mets
):
    """Test that trying to generate SIP from invalid path raises error."""
    with pytest.raises(ValueError) as error:
        SIP.from_directory(filepath, simple_mets)
    assert str(error.value) == error_message


def test_generated_sip_digital_provenance(simple_mets):
    """Test that SIP generated from directory has siptools-ng represented in
    the digital provenance metadata.
    """
    sip = SIP.from_directory(
        directory_path="tests/data/generate_sip_from_directory/data",
        mets=simple_mets
    )

    structural_map = sip.mets.structural_maps.pop()
    root_div = structural_map.root_div

    structmap_creation_event = next(
        metadata for metadata in root_div.metadata
        if isinstance(metadata, DigitalProvenanceEventMetadata)
        and metadata.event_type == "creation"
    )

    linked_agents = (
        agent.agent_metadata
        for agent in structmap_creation_event.linked_agents
    )

    siptools_ng_agent = digital_provenance.get_siptools_ng_agent()
    assert siptools_ng_agent in root_div.metadata
    assert siptools_ng_agent in linked_agents
