"""Test SIPs."""
import hashlib
import tarfile
from pathlib import Path

import lxml
import pytest
from mets_builder import METS, MetsProfile
from mets_builder.digital_object import DigitalObject
from mets_builder.metadata import (DigitalProvenanceAgentMetadata,
                                   DigitalProvenanceEventMetadata,
                                   ImportedMetadata,
                                   Metadata,
                                   MetadataFormat,
                                   MetadataType)
from mets_builder.structural_map import StructuralMapDiv
from utils import find_metadata

import siptools_ng.agent
from siptools_ng.file import File
from siptools_ng.sip import SIP, _structural_map_from_directory_structure


def _extract_sip(digital_object_path, extract_filepath):
    """Extract tarred SIP to given path."""
    with tarfile.open(digital_object_path) as sip:
        sip.extractall(extract_filepath)


def _get_testing_filepaths(tmp_path_of_test):
    """Get filepaths for directing files produced by the tests to a canonized
    location.
    """
    output_filepath = tmp_path_of_test / "finalized_sip.tar"
    extracted_filepath = tmp_path_of_test / "extracted_sip"
    return output_filepath, extracted_filepath


def _check_shared_metadata(div: StructuralMapDiv) -> bool:
    """Check if all subdivs and digital object contain any shared metadata."""
    # Pick a child randomly to check against the other children.
    child = (div.digital_objects | div.divs).pop()
    metadata = set(metadata for metadata in child.metadata
                   if metadata.metadata_type != MetadataType.TECHNICAL)

    for child in div.digital_objects | div.divs:
        if len(child.metadata & metadata) == 0:
            return False

    return True


def test_creating_sip_with_zero_files(simple_mets):
    """Test that creating a SIP with zero files results in error."""
    sip = SIP(mets=simple_mets, files=[])

    with pytest.raises(ValueError) as error:
        sip.finalize(
            output_filepath="sip.tar",
            sign_key_filepath="tests/data/rsa-keys.crt"
        )
    assert str(error.value) == "SIP does not contain any digital objects."
    assert len(sip.mets.structural_maps) == 0


def test_default_structural_map(simple_mets, files):
    """Test that the default structural map is generated."""
    sip = SIP.from_files(mets=simple_mets, files=files)
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
    according to the directory structure. The label of each div should be the
    corresponding directory name and the type should be "directory". The file
    is not represented with a div, but as a DigitalObject stored in the correct
    div.

    The root div should be an additional wrapping div with type 'directory'.
    """
    file1 = File(path="tests/data/test_file.txt",
                 digital_object_path="data/a/file1.txt")
    file2 = File(path="tests/data/test_file.txt",
                 digital_object_path="data/a/file2.txt")
    file3 = File(path="tests/data/test_file.txt",
                 digital_object_path="data/b/very/long/chain/file3.txt")
    files = (file1, file2, file3)

    structural_map = _structural_map_from_directory_structure(files)

    assert structural_map.structural_map_type == 'PHYSICAL'

    # defined directory structure is wrapped in a root div with type
    # "directory"
    root_div = structural_map.root_div
    assert root_div.div_type == "directory"
    assert len(root_div.divs) == 1

    # root of the user defined tree is a directory called "data", containing
    # two other directories
    data_div = root_div.divs.pop()
    assert data_div.label == "data"
    assert len(data_div.divs) == 2

    # directory "a" in "data" contains digital objects 1 and 2
    a_div = next(div for div in data_div if div.label == "a")
    # assert a_div.digital_objects == {do1, do2}

    # directory "a" contains 2 file divs
    assert len(a_div.divs) == 2

    # the file divs of directory "a" contain the corresponding digital objects.
    file1_div = next(div for div in a_div.divs if div.label == "file1.txt")
    assert file1_div.digital_objects == {file1.digital_object}
    assert file1_div.div_type == "file"

    file2_div = next(div for div in a_div.divs if div.label == "file2.txt")
    assert file2_div.digital_objects == {file2.digital_object}
    assert file2_div.div_type == "file"

    # directory "b" in "data" has a deep directory structure, at the bottom of
    # which is digital object 3
    b_div = next(div for div in data_div if div.label == "b")

    very_div = b_div.divs.pop()
    assert very_div.label == "very"
    assert very_div.div_type == "directory"

    long_div = very_div.divs.pop()
    assert long_div.label == "long"
    assert long_div.div_type == "directory"

    chain_div = long_div.divs.pop()
    assert chain_div.label == "chain"
    assert long_div.div_type == "directory"

    assert len(chain_div.divs) == 1

    file3_div = next(div for div in chain_div.divs if div.label == "file3.txt")
    assert file3_div.digital_objects == {file3.digital_object}
    assert file3_div.div_type == "file"


def test_generating_structural_map_with_no_digital_objects():
    """Test that generating structural map with zero digital objects raises an
    error.
    """
    with pytest.raises(ValueError) as error:
        _structural_map_from_directory_structure([])
    assert str(error.value) == (
        "Given 'files' is empty. Structural map can not be "
        "generated with zero digital objects."
    )


def test_generating_structural_map_digital_provenance(simple_mets):
    """Test that digital provenance metadata is created correctly when
    structural map is generated.

    Event (structmap generation) and agents (dpres-siptools-ng and
    dpres-mets-builder) should have been added to the root div of the
    generated structural map. The agents should also be linked to the
    event as the executing program.
    """
    file = File(path="tests/data/test_file.txt",
                digital_object_path="data/file.txt")
    sip = SIP.from_files(mets=simple_mets, files=[file])

    root_div = sip.default_struct_map.root_div

    # Event
    creation_events = [
        metadata for metadata in root_div.metadata
        if isinstance(metadata, DigitalProvenanceEventMetadata)
        and metadata.event_type == "creation"
    ]
    assert len(creation_events) == 1
    event = creation_events[0]
    assert event.event_type == "creation"
    assert event.detail == (
        "Creation of structural metadata with the "
        "StructuralMap.from_directory_structure method"
    )
    assert event.outcome.value == "success"
    assert event.outcome_detail == (
        "Created METS structural map with type 'PHYSICAL'"
    )
    assert event.event_identifier_type == "UUID"
    assert event.event_identifier is None
    assert event.datetime is None

    # Two agents should be linked to structmap creation event
    assert len(event.linked_agents) == 2
    for agent in event.linked_agents:
        assert agent.agent_role == "executing program"

    # The agents should be mets-builder and siptools-ng
    agent_mds = [agent.agent_metadata for agent in event.linked_agents]
    assert {agent_md.name for agent_md in agent_mds} \
        == {"dpres-mets-builder", "dpres-siptools-ng"}

    # Also the linked agents have been added to root_div
    for agent_md in agent_mds:
        assert agent_md in root_div.metadata


class DummyMetadata(Metadata):
    """Dummy digital provenance metadata."""

    def __init__(self, identifier):
        """Init dummy metadata."""
        super().__init__(
            metadata_format="OTHER",
            other_format="dummy format",
            metadata_type="digital provenance",
            format_version=None,
            identifier=identifier
        )

    def _to_xml_element_tree():
        """Do nothing."""


class DummyDescriptiveMetadata(Metadata):
    """Dummy digital provenance metadata."""

    def __init__(self, identifier):
        """Init dummy metadata."""
        super().__init__(
            metadata_format="OTHER",
            other_format="dummy format",
            metadata_type="descriptive",
            format_version=None,
            identifier=identifier
        )

    def _to_xml_element_tree():
        """Do nothing."""


@pytest.mark.parametrize(
    "metadata_class",
    [DummyMetadata, DummyDescriptiveMetadata]
)
def test_add_metadata_to_sip(simple_sip, metadata_class):
    """Test adding metadata to SIP.

    Metadata should be added to root div of default structural map.
    """
    simple_sip.add_metadata([metadata_class('test-id')])
    added_md = find_metadata(simple_sip.default_struct_map.root_div,
                             metadata_class)
    assert added_md.identifier == "test-id"

    # Metada import event should not be generated
    events = [md for md in simple_sip.default_struct_map.root_div.metadata
              if isinstance(md, DigitalProvenanceEventMetadata)]
    for event in events:
        assert event.event_type != "metadata extraction"


def test_add_imported_metadata_to_sip(simple_mets):
    """Test adding imported metadata to SIP.

    Metadata import event should be added to sip.
    """
    # TODO: Is this file required? Could empty SIP work?
    file = File(path="tests/data/test_file.txt",
                digital_object_path="test_file.txt")
    sip=SIP.from_files(mets=simple_mets, files=[file])

    div = sip.default_struct_map.root_div

    metadata = ImportedMetadata(
        metadata_type=MetadataType.DESCRIPTIVE,
        metadata_format=MetadataFormat.OTHER,
        other_format="PAS-special",
        format_version="1.0",
        data_path="tests/data/imported_metadata.xml"
    )
    sip.add_metadata([metadata])
    assert metadata in div.metadata
    # In addtition to the added metadata, the div should contain event metadata
    events = [md for md in div.metadata
              if isinstance(md, DigitalProvenanceEventMetadata)]
    metadata_import_events = [
        event for event in events
        if event.detail == "Descriptive metadata import from external source"
    ]
    assert len(metadata_import_events) == 1
    assert metadata_import_events[0].event_type == 'metadata extraction'
    assert metadata_import_events[0].datetime is None
    assert metadata_import_events[0].detail \
        == "Descriptive metadata import from external source"
    assert metadata_import_events[0].outcome.value == "success"
    assert metadata_import_events[0].outcome_detail \
        == "Descriptive metadata imported to mets dmdSec from external source"


def test_add_descriptive_metadata_to_file(simple_mets):
    """Test adding a file with descriptive metadata.

    If a file contains descriptive metadata, the descriptive metadata
    should be inserted to default structural map.
    """
    descriptive_md = DummyDescriptiveMetadata(identifier="test-id")

    file_with_metadata = File(path="tests/data/test_file.txt",
                              digital_object_path='with_md')
    file_with_metadata.add_metadata([descriptive_md])
    file_without_metadata = File(path="tests/data/test_file.txt",
                                 digital_object_path='without_md')
    sip = SIP.from_files(
        mets=simple_mets,
        files=[file_with_metadata, file_without_metadata]
    )

    # Root div should contain one div for each file. One of the divs
    # should contain descriptive metadata, the other should not.
    divs = list(sip.default_struct_map.root_div.divs)
    assert len(divs) == 2
    for div in divs:
        if div.label == "with_md":
            assert descriptive_md in div.metadata
            # The div should not contain any other metadata
            assert len(div.metadata) == 1
        elif div.label == "without_md":
            assert not div.metadata
        else:
            raise ValueError("Unexpected label")


def test_add_imported_metadata_to_file(simple_mets):
    """Test adding a file with imported metadata.

    Metadata import event should be added to div of file in default
    structural map.
    """
    imported_md = ImportedMetadata(
        metadata_type=MetadataType.DESCRIPTIVE,
        metadata_format=MetadataFormat.OTHER,
        other_format="PAS-special",
        format_version="1.0",
        data_path="tests/data/imported_metadata.xml"
    )

    file_with_metadata = File(path="tests/data/test_file.txt",
                              digital_object_path='with_md')
    file_with_metadata.add_metadata([imported_md])
    file_without_metadata = File(path="tests/data/test_file.txt",
                                 digital_object_path='without_md')
    sip = SIP.from_files(
        mets=simple_mets,
        files=[file_with_metadata, file_without_metadata]
    )

    # Root div should contain one div for each file. One of the divs
    # should contain descriptive metadata and PREMIS event that
    # describes metadata import. The other div should not contain any
    # metadata.
    divs = list(sip.default_struct_map.root_div.divs)
    assert len(divs) == 2
    for div in divs:
        if div.label == "with_md":
            assert len(div.metadata) == 2
            assert imported_md in div.metadata
            event = next(iter(div.metadata - {imported_md}))
            assert event.detail \
                == "Descriptive metadata import from external source"
        elif div.label == "without_md":
            assert not div.metadata
        else:
            raise ValueError("Unexpected label")


def test_metadata_deep_bundling(simple_mets):
    """Test that shared event metadata is bundled to the structural map div
    with a deep SIP directory structure.
    """
    files = {
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
            digital_object_path="div1/test_csv.csv"
        ),
        File(
            path="tests/data/test_image.tif",
            digital_object_path="div2/test_image.tif"
        ),
        File(
            path="tests/data/test_video.dv",
            digital_object_path="div2/div3/test_video.dv"
        ),
        File(
            path="tests/data/test_video_ffv_flac.mkv",
            digital_object_path="div2/div3/test_video_ffv_flac.mkv"
        )
    }
    sip = SIP.from_files(mets=simple_mets, files=files)

    # test for root_div
    root_div = list(sip.mets.structural_maps)[0].root_div
    assert not _check_shared_metadata(root_div)
    assert len({div for div in root_div.divs if div.div_type == "file"}) == 2
    assert len({div for div in root_div.divs if div.div_type == "directory"}) \
        == 2

    agent_names = {element.name for element in root_div.metadata
                   if isinstance(element, DigitalProvenanceAgentMetadata)}
    expected_agent_names = {'SiardDetector', 'file-scraper', 'SegYDetector',
                            'ResultsMergeScraper', 'PredefinedDetector',
                            'dpres-siptools-ng', 'dpres-mets-builder',
                            'MimeMatchScraper', 'ODFDetector', 'MagicDetector',
                            'FidoDetector'}
    assert agent_names >= expected_agent_names

    event_types = {element.event_type for element in root_div.metadata
                   if isinstance(element, DigitalProvenanceEventMetadata)}
    expected_event_types = {'creation', 'message digest calculation'}
    assert event_types >= expected_event_types

    # test root_div/div1
    div1 = next(div for div in root_div.divs if div.label == "div1")
    assert not _check_shared_metadata(div1)
    assert len({div for div in div1.divs if div.div_type == "file"}) == 1
    assert len({div for div in div1.divs if div.div_type == "directory"}) == 0

    agent_names = {element.name for element in div1.metadata
                   if isinstance(element, DigitalProvenanceAgentMetadata)}
    expected_agent_names = {'CsvScraper', 'MagicTextScraper',
                            'TextEncodingMetaScraper'}
    assert agent_names >= expected_agent_names

    event_types = {element.event_type for element in div1.metadata
                   if isinstance(element, DigitalProvenanceEventMetadata)}
    expected_event_types = {'format identification', 'metadata extraction'}
    assert event_types >= expected_event_types

    # test root_div/div2
    div2 = next(div for div in root_div.divs if div.label == "div2")
    assert not _check_shared_metadata(div2)
    assert len({div for div in div2.divs if div.div_type == "file"}) == 1
    assert len({div for div in div2.divs if div.div_type == "directory"}) == 1
    agent_names = {element.name for element in div2.metadata
                   if isinstance(element, DigitalProvenanceAgentMetadata)}
    expected_agent_names = set()
    assert agent_names >= expected_agent_names

    event_types = {element.event_type for element in div2.metadata
                   if isinstance(element, DigitalProvenanceEventMetadata)}
    expected_event_types = set()
    assert event_types >= expected_event_types

    # test root_div/div2/div3
    div3 = next(div for div in div2.divs if div.label == "div3")
    assert not _check_shared_metadata(div3)
    assert len({div for div in div3.divs if div.div_type == "file"}) == 2
    assert len({div for div in div3.divs if div.div_type == "directory"}) == 0
    agent_names = {element.name for element in div3.metadata
                   if isinstance(element, DigitalProvenanceAgentMetadata)}
    expected_agent_names = {'MediainfoScraper'}
    assert agent_names >= expected_agent_names

    event_types = {element.event_type for element in div3.metadata
                   if isinstance(element, DigitalProvenanceEventMetadata)}
    expected_event_types = {'metadata extraction', 'format identification'}
    assert event_types >= expected_event_types


def test_metadata_bundling(simple_sip):
    """Test that shared event metadata is bundled to the structural map div.
    """
    root_div = next(map.root_div for map in simple_sip.mets.structural_maps
                    if map.root_div.div_type != "test_div")
    assert not _check_shared_metadata(root_div)
    assert len({div for div in root_div.divs if div.div_type == "file"}) == 3
    assert len({div for div in root_div.divs if div.div_type == "directory"}) \
        == 0

    agent_names = {element.name for element in root_div.metadata
                   if isinstance(element, DigitalProvenanceAgentMetadata)}
    expected_agent_names = {'SiardDetector', 'file-scraper', 'SegYDetector',
                            'ResultsMergeScraper', 'PredefinedDetector',
                            'dpres-siptools-ng', 'dpres-mets-builder',
                            'MimeMatchScraper', 'ODFDetector', 'MagicDetector',
                            'FidoDetector'}
    assert agent_names >= expected_agent_names

    event_types = {element.event_type for element in root_div.metadata
                   if isinstance(element, DigitalProvenanceEventMetadata)}
    expected_event_types = {'format identification',
                            'message digest calculation', 'creation'}
    assert event_types >= expected_event_types
