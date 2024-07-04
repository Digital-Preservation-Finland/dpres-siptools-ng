"""Test SIPs."""
import hashlib
import tarfile
import lxml
import pytest

import siptools_ng.agent

from siptools_ng.sip import (SIP,
                             structural_map_from_directory_structure,
                             _add_metadata)
from mets_builder import METS, MetsProfile
from mets_builder.digital_object import DigitalObject
from mets_builder.structural_map import StructuralMapDiv
from mets_builder.metadata import (DigitalProvenanceAgentMetadata,
                                   DigitalProvenanceEventMetadata,
                                   ImportedMetadata, Metadata,
                                   MetadataFormat, MetadataType)


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
    sip = SIP(mets=mets, digital_objects=[])

    with pytest.raises(ValueError) as error:
        sip.finalize(
            output_filepath="sip.tar",
            sign_key_filepath="tests/data/rsa-keys.crt"
        )
    assert str(error.value) == "SIP does not contain any digital objects."
    assert len(sip.mets.structural_maps) == 0


def test_default_structural_map(simple_mets, digital_objects):
    """Test that the default structural map is generated."""
    sip = SIP(mets=simple_mets, digital_objects=digital_objects)
    assert len(sip.mets.structural_maps) == 1


def test_simple_sip(simple_sip):
    """Test that simple sip has the default structural map."""
    assert len(simple_sip.mets.structural_maps) == 2


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

    mets = lxml.etree.parse(str(mets_filepath))
    mets.getroot().tag = "{http://www.loc.gov/METS/}mets"


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

    siptools_ng_agent = siptools_ng.agent.get_siptools_ng_agent()
    assert siptools_ng_agent in root_div.metadata
    assert siptools_ng_agent in linked_agents


def test_generating_structural_map_from_directory():
    """Test generating structural map from directory contents.

    There should be a div for each directory, and the divs should be nested
    according to the directory structure. The type of each div should be the
    corresponding directory name. The file is not represented with a div, but
    as a DigitalObject stored in the correct div.

    The root div should be an additional wrapping div with type 'directory'.
    """
    do1 = DigitalObject(sip_filepath="data/a/file1.txt")
    do2 = DigitalObject(sip_filepath="data/a/file2.txt")
    do3 = DigitalObject(sip_filepath="data/b/deep/directory/chain/file3.txt")
    digital_objects = (do1, do2, do3)

    structural_map = structural_map_from_directory_structure(digital_objects)

    assert structural_map.structural_map_type == 'PHYSICAL'

    # defined directory structure is wrapped in a root div with type
    # "directory"
    root_div = structural_map.root_div
    assert root_div.div_type == "directory"
    assert len(root_div.divs) == 1

    # root of the user defined tree is a directory called "data", containing
    # two other directories
    data_div = root_div.divs.pop()
    assert data_div.div_type == "data"
    assert len(data_div.divs) == 2

    # directory "a" in "data" contains digital objects 1 and 2
    a_div = next(div for div in data_div if div.div_type == "a")
    assert a_div.digital_objects == {do1, do2}

    # directory "b" in "data" has a deep directory structure, at the bottom of
    # which is digital object 3
    b_div = next(div for div in data_div if div.div_type == "b")
    deep_div = b_div.divs.pop()
    assert deep_div.div_type == "deep"
    directory_div = deep_div.divs.pop()
    assert directory_div.div_type == "directory"
    chain_div = directory_div.divs.pop()
    assert chain_div.div_type == "chain"
    assert chain_div.digital_objects == {do3}


def test_generating_structural_map_with_no_digital_objects():
    """Test that generating structural map with zero digital objects raises an
    error.
    """
    with pytest.raises(ValueError) as error:
        structural_map_from_directory_structure([])
    assert str(error.value) == (
        "Given 'digital_objects' is empty. Structural map can not be "
        "generated with zero digital objects."
    )


def test_generating_structural_map_digital_provenance():
    """Test that digital provenance metadata is created correctly when
    structural map is generated.

    Event (structmap generation) and agent (dpres-mets-builder) should have
    been added to the root div of the generated structural map. The agent
    should also be linked to the event as the executing program.
    """
    digital_object = DigitalObject(sip_filepath="data/file.txt")
    structural_map = structural_map_from_directory_structure([digital_object])

    root_div = structural_map.root_div
    assert len(root_div.metadata) == 2

    # Event
    event = next(
        metadata for metadata in root_div.metadata
        if isinstance(metadata, DigitalProvenanceEventMetadata)
    )
    assert event.event_type == "creation"
    assert event.event_detail == (
        "Creation of structural metadata with the "
        "StructuralMap.from_directory_structure method"
    )
    assert event.event_outcome.value == "success"
    assert event.event_outcome_detail == (
        "Created METS structural map with type 'PHYSICAL'"
    )
    assert event.event_identifier_type == "UUID"
    assert event.event_identifier is None
    assert event.event_datetime is None

    # Agent
    assert len(event.linked_agents) == 1
    linked_agent = event.linked_agents[0]
    assert linked_agent.agent_role == "executing program"
    assert linked_agent.agent_metadata.agent_name == "dpres-mets-builder"

    agent_in_div = next(
        metadata for metadata in root_div.metadata
        if isinstance(metadata, DigitalProvenanceAgentMetadata)
    )
    assert agent_in_div == linked_agent.agent_metadata


def test_generating_structural_map_digital_provenance_with_custom_agents():
    """Test that custom agents can be added to generated structural map.

    The agents should have been added to the root div of the generated
    structural map. The agents should also be linked to the structmap creation
    event as executing programs.
    """
    digital_object = DigitalObject(sip_filepath="data/file.txt")
    custom_agent_1 = DigitalProvenanceAgentMetadata(
        agent_name="custom_agent_1",
        agent_version="1.0",
        agent_type="software"
    )
    custom_agent_2 = DigitalProvenanceAgentMetadata(
        agent_name="custom_agent_2",
        agent_version="1.0",
        agent_type="software"
    )

    structural_map = structural_map_from_directory_structure(
        [digital_object],
        additional_agents=[custom_agent_1, custom_agent_2]
    )

    root_div = structural_map.root_div
    mets_builder = DigitalProvenanceAgentMetadata.get_mets_builder_agent()
    assert mets_builder in root_div.metadata
    assert custom_agent_1 in root_div.metadata
    assert custom_agent_2 in root_div.metadata

    event = next(
        metadata for metadata in root_div.metadata
        if isinstance(metadata, DigitalProvenanceEventMetadata)
    )
    linked_agents = (agent.agent_metadata for agent in event.linked_agents)
    assert mets_builder in linked_agents
    assert custom_agent_1 in linked_agents
    assert custom_agent_2 in linked_agents


def test_add_metadata_to_div():
    """Test adding metadata to a structural map division."""
    div = StructuralMapDiv(div_type="test_type")
    assert div.metadata == set()

    metadata = Metadata(
        metadata_type=MetadataType.DESCRIPTIVE,
        metadata_format=MetadataFormat.OTHER,
        other_format="PAS-special",
        format_version="1.0",
    )
    _add_metadata(div, metadata)
    assert div.metadata == {metadata}


def test_add_imported_metadata_to_div():
    """Test adding imported metadata to a structural map division.

    Metadata import event should be added to div.
    """
    div = StructuralMapDiv(div_type="test_type")
    assert div.metadata == set()

    metadata = ImportedMetadata(
        metadata_type=MetadataType.DESCRIPTIVE,
        metadata_format=MetadataFormat.OTHER,
        other_format="PAS-special",
        format_version="1.0",
        data_path="tests/data/imported_metadata.xml"
    )
    _add_metadata(div, metadata)
    # In addtition to the added metadata, the div should contain event metadata
    assert len(div.metadata) == 2
    assert metadata in div.metadata
    event_metadata = (div.metadata - {metadata}).pop()
    assert event_metadata.event_type == 'metadata extraction'
    assert event_metadata.event_datetime is None
    assert event_metadata.event_detail \
        == "Descriptive metadata import from external source"
    assert event_metadata.event_outcome.value == "success"
    assert event_metadata.event_outcome_detail\
        == "Descriptive metadata imported to mets dmdSec from external source"
