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
                                   ImportedMetadata, MetadataFormat,
                                   MetadataType)
from mets_builder.structural_map import StructuralMapDiv
from utils import find_metadata

import siptools_ng.agent
from siptools_ng.file import File
from siptools_ng.sip import (SIP, _add_metadata,
                             _structural_map_from_directory_structure)


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


def test_creating_sip_with_zero_files():
    """Test that creating a SIP with zero files results in error."""
    mets = METS(
        mets_profile=MetsProfile.CULTURAL_HERITAGE,
        contract_id="contract_id",
        creator_name="Mr. Foo",
        creator_type="INDIVIDUAL"
    )
    sip = SIP(mets=mets, files=[])

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
    do1 = DigitalObject(path="data/a/file1.txt")
    do2 = DigitalObject(path="data/a/file2.txt")
    do3 = DigitalObject(path="data/b/very/long/chain/file3.txt")
    digital_objects = (do1, do2, do3)

    structural_map = _structural_map_from_directory_structure(digital_objects)

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
    assert file1_div.digital_objects == {do1}
    assert file1_div.div_type == "file"

    file2_div = next(div for div in a_div.divs if div.label == "file2.txt")
    assert file2_div.digital_objects == {do2}
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
    assert file3_div.digital_objects == {do3}
    assert file3_div.div_type == "file"


def test_generating_structural_map_with_no_digital_objects():
    """Test that generating structural map with zero digital objects raises an
    error.
    """
    with pytest.raises(ValueError) as error:
        _structural_map_from_directory_structure([])
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
    digital_object = DigitalObject(path="data/file.txt")
    structural_map = _structural_map_from_directory_structure([digital_object])

    root_div = structural_map.root_div
    assert len(root_div.metadata) == 2

    # Event
    event = next(
        metadata for metadata in root_div.metadata
        if isinstance(metadata, DigitalProvenanceEventMetadata)
    )
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

    # Agent
    assert len(event.linked_agents) == 1
    linked_agent = event.linked_agents[0]
    assert linked_agent.agent_role == "executing program"
    assert linked_agent.agent_metadata.name == "dpres-mets-builder"

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
    digital_object = DigitalObject(path="data/file.txt")
    custom_agent_1 = DigitalProvenanceAgentMetadata(
        name="custom_agent_1",
        version="1.0",
        agent_type="software"
    )
    custom_agent_2 = DigitalProvenanceAgentMetadata(
        name="custom_agent_2",
        version="1.0",
        agent_type="software"
    )

    structural_map = _structural_map_from_directory_structure(
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
    event_metadata = find_metadata(div, DigitalProvenanceEventMetadata)
    assert event_metadata.event_type == 'metadata extraction'
    assert event_metadata.datetime is None
    assert event_metadata.detail \
        == "Descriptive metadata import from external source"
    assert event_metadata.outcome.value == "success"
    assert event_metadata.outcome_detail \
        == "Descriptive metadata imported to mets dmdSec from external source"


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


@pytest.mark.parametrize(
    "method_name,kwargs",
    (
        (
            "from_files",
            {
                "metadata_xml_paths": ["tests/data/valid_ead3.xml"]
            }
        ),
        (
            "from_files",
            {
                "metadata_xml_strings": [
                    Path("tests/data/valid_ead3.xml").read_bytes()
                ]
            }
        ),
        (
            "from_directory",
            {
                "metadata_xml_paths": ["tests/data/valid_ead3.xml"]
            }
        ),
        (
            "from_directory",
            {
                "metadata_xml_strings": [
                    Path("tests/data/valid_ead3.xml").read_bytes()
                ]
            }
        )
    )
)
def test_xml_metadata_import_to_struct_map(
        simple_mets, files, method_name, kwargs):
    """
    Test that XML metadata given to `SIP.from_directory` is
    automatically detected, imported and linked to the root of the
    automatically generated structural map
    """
    kwargs = kwargs.copy()

    kwargs["mets"] = simple_mets
    if method_name == "from_files":
        sip_factory_method = SIP.from_files

        kwargs["files"] = files
    elif method_name == "from_directory":
        sip_factory_method = SIP.from_directory

        kwargs["directory_path"] = "tests/data/generate_sip_from_directory/data"

    sip = sip_factory_method(**kwargs)
    mets = sip.mets

    assert len(mets.structural_maps) == 1
    struct_map = list(mets.structural_maps)[0]

    imported_metadata = next(
        metadata for metadata in struct_map.root_div.metadata
        if isinstance(metadata, ImportedMetadata)
    )

    assert imported_metadata.is_descriptive
    assert imported_metadata.other_format == "EAD3"

    if "metadata_xml_strings" in kwargs:
        assert b"<ead " in imported_metadata.data_string
    else:
        assert imported_metadata.data_path == \
            Path(kwargs["metadata_xml_paths"][0]).resolve()
