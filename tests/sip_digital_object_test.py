"""Test SIPDigitalObject."""
import itertools
from datetime import datetime

import file_scraper
import pytest
from mets_builder.metadata import (DigitalProvenanceAgentMetadata,
                                   DigitalProvenanceEventMetadata,
                                   TechnicalAudioMetadata,
                                   TechnicalCSVMetadata,
                                   TechnicalImageMetadata,
                                   TechnicalFileObjectMetadata,
                                   TechnicalBitstreamObjectMetadata,
                                   TechnicalVideoMetadata)

from siptools_ng.sip_digital_object import (MetadataGenerationError,
                                            SIPDigitalObject)
from utils import find_metadata


@pytest.mark.parametrize(
    "source_filepath",
    [
        # Source filepath does not exist
        ("tests/data/nonexistent_test_file.txt"),
        # Source filepath is a directory
        ("tests/data")
    ]
)
def test_digital_object_source_filepath_validity(source_filepath):
    """Test that invalid source filepath raises error."""
    with pytest.raises(ValueError) as error:
        SIPDigitalObject(
            source_filepath=source_filepath,
            sip_filepath="sip_data/test_file.txt"
        )
    assert "is not a file." in str(error.value)


def test_resolve_symbolic_link_as_source_filepath():
    """Test that if symbolic link is given as source filepath, it is resolved
    to the orginal file.
    """
    digital_object = SIPDigitalObject(
        source_filepath="tests/data/symbolic_link_to_test_file",
        sip_filepath="sip_data/test_file.txt"
    )
    assert not digital_object.source_filepath.is_symlink()
    assert digital_object.source_filepath.is_file()


def test_generating_technical_metadata_for_text_file():
    """Test that generating technical metadata for a text file results in
    correct information.
    """
    digital_object = SIPDigitalObject(
        source_filepath="tests/data/test_file.txt",
        sip_filepath="sip_data/test_file.txt"
    )

    digital_object.generate_technical_metadata()
    assert digital_object.use is None

    metadata = find_metadata(digital_object, TechnicalFileObjectMetadata)
    assert metadata.file_format == "text/plain"
    assert metadata.file_format_version == "(:unap)"
    assert metadata.charset.value == "UTF-8"
    assert metadata.checksum_algorithm.value == "MD5"
    assert metadata.checksum == "d8e8fca2dc0f896fd7cb4cb0031ba249"
    assert metadata.original_name == "test_file.txt"

    # File creation date cannot be tested with hardcoded time, because it will
    # differ according to when the user has cloned the repository (and created
    # the test file while doing so). Settle for testing that file creation date
    # is in ISO format
    format_string = "%Y-%m-%dT%H:%M:%S"
    # Raises error if file_created_date doesn't follow the right format
    datetime.strptime(metadata.file_created_date, format_string)


def test_generating_technical_metadata_for_image():
    """Test that generating technical metadata for an image results in correct
    information.
    """
    digital_object = SIPDigitalObject(
        source_filepath="tests/data/test_image.tif",
        sip_filepath="sip_data/test_image.tif"
    )

    digital_object.generate_technical_metadata()

    metadata = find_metadata(digital_object, TechnicalFileObjectMetadata)
    assert metadata.file_format == "image/tiff"
    assert metadata.file_format_version == "6.0"
    assert metadata.charset is None
    assert metadata.checksum_algorithm.value == "MD5"
    assert metadata.checksum == "1559aa902da28ffe2cb55f6319c963f3"
    assert metadata.original_name == "test_image.tif"

    # File creation date cannot be tested with hardcoded time, because it will
    # differ according to when the user has cloned the repository (and created
    # the test file while doing so). Settle for testing that file creation date
    # is in ISO format
    format_string = "%Y-%m-%dT%H:%M:%S"
    # Raises error if file_created_date doesn't follow the right format
    datetime.strptime(metadata.file_created_date, format_string)

    metadata = find_metadata(digital_object, TechnicalImageMetadata)
    assert metadata.compression == "zip"
    assert metadata.colorspace == "rgb"
    assert metadata.width == "10"
    assert metadata.height == "6"
    assert metadata.bps_value == "8"
    assert metadata.bps_unit == "integer"
    assert metadata.samples_per_pixel == "3"
    assert metadata.mimetype == "image/tiff"
    assert metadata.byte_order == "little endian"
    assert metadata.icc_profile_name == "(:unav)"


def test_generating_technical_metadata_multiple_times():
    """Test that it is not possible to generate technical metadata multiple
    times.
    """
    digital_object = SIPDigitalObject(
        source_filepath="tests/data/test_file.txt",
        sip_filepath="sip_data/test_file.txt"
    )
    digital_object.generate_technical_metadata()

    with pytest.raises(MetadataGenerationError) as error:
        digital_object.generate_technical_metadata()
    assert str(error.value) == (
        "Technical metadata has already been generated for the digital object."
    )


def test_generating_technical_metadata_for_audio():
    """Test that generating technical metadata for an audio file results in
    correct information.
    """
    digital_object = SIPDigitalObject(
        source_filepath="tests/data/test_audio.wav",
        sip_filepath="sip_data/test_audio.wav"
    )

    digital_object.generate_technical_metadata()

    metadata = find_metadata(digital_object, TechnicalFileObjectMetadata)
    assert metadata.file_format == "audio/x-wav"
    assert metadata.file_format_version == "(:unap)"
    assert metadata.charset is None
    assert metadata.checksum_algorithm.value == "MD5"
    assert metadata.checksum == "cd14de04e3490de9f6f234fb10cd4885"
    assert metadata.original_name == "test_audio.wav"

    # File creation date cannot be tested with hardcoded time, because it will
    # differ according to when the user has cloned the repository (and created
    # the test file while doing so). Settle for testing that file creation date
    # is in ISO format
    format_string = "%Y-%m-%dT%H:%M:%S"
    # Raises error if file_created_date doesn't follow the right format
    datetime.strptime(metadata.file_created_date, format_string)

    metadata = find_metadata(digital_object, TechnicalAudioMetadata)
    assert metadata.audio_data_encoding == "PCM"
    assert metadata.bits_per_sample == "8"
    assert metadata.codec_creator_app == "Lavf56.40.101"
    assert metadata.codec_creator_app_version == "56.40.101"
    assert metadata.codec_name == "PCM"
    assert metadata.codec_quality.value == "lossless"
    assert metadata.data_rate == "706"
    assert metadata.data_rate_mode.value == "Fixed"
    assert metadata.sampling_frequency == "44.1"
    assert metadata.duration == "PT0.86S"
    assert metadata.num_channels == "2"


def test_generating_technical_metadata_for_video():
    """Test that generating technical metadata for an video file results in
    correct information.
    """
    digital_object = SIPDigitalObject(
        source_filepath="tests/data/test_video.dv",
        sip_filepath="sip_data/test_video.dv"
    )

    digital_object.generate_technical_metadata()

    metadata = find_metadata(digital_object, TechnicalFileObjectMetadata)
    assert metadata.file_format == "video/dv"
    assert metadata.file_format_version == "(:unap)"
    assert metadata.charset is None
    assert metadata.checksum_algorithm.value == "MD5"
    assert metadata.checksum == "646912efe14a049ceb9f3a6f741d7b66"
    assert metadata.original_name == "test_video.dv"

    # File creation date cannot be tested with hardcoded time, because it will
    # differ according to when the user has cloned the repository (and created
    # the test file while doing so). Settle for testing that file creation date
    # is in ISO format
    format_string = "%Y-%m-%dT%H:%M:%S"
    # Raises error if file_created_date doesn't follow the right format
    datetime.strptime(metadata.file_created_date, format_string)

    # Technical video metadata
    metadata = [
        data for data in digital_object.metadata
        if isinstance(data, TechnicalVideoMetadata)
    ][0]
    assert metadata.duration == "PT0.08S"
    assert metadata.data_rate == "24.4416"
    assert metadata.bits_per_sample == "8"
    assert metadata.color.value == "Color"
    assert metadata.codec_creator_app == "(:unav)"
    assert metadata.codec_creator_app_version == "(:unav)"
    assert metadata.codec_name == "DV"
    assert metadata.codec_quality.value == "lossy"
    assert metadata.data_rate_mode.value == "Fixed"
    assert metadata.frame_rate == "25"
    assert metadata.pixels_horizontal == "720"
    assert metadata.pixels_vertical == "576"
    assert metadata.par == "1.422"
    assert metadata.dar == "1.778"
    assert metadata.sampling == "4:2:0"
    assert metadata.signal_format == "PAL"
    assert metadata.sound.value == "No"


def test_generate_technical_metadata_for_video_container():
    """
    Test that generating technical metadata for a video contaier results
    in correct information and linkings
    """
    digital_object = SIPDigitalObject(
        source_filepath="tests/data/test_video_ffv_flac.mkv",
        sip_filepath="sip_data/test_video_ffv_flac.mkv"
    )
    digital_object.generate_technical_metadata()

    # Get a flat list of all technical metadata objects; we'll verify their
    # relationship later.
    metadatas = list(
        # Flatten the list of metadata objects for each stream
        itertools.chain.from_iterable([
            stream.metadata for stream in digital_object.streams
        ])
    ) + list(digital_object.metadata)

    # Three technical metadata objects are created
    ffv_bitstream = next(
        metadata for metadata in metadatas
        if isinstance(metadata, TechnicalBitstreamObjectMetadata)
        and metadata.file_format == "video/x-ffv"
    )
    assert ffv_bitstream.file_format_version == "3"

    flac_bitstream = next(
        metadata for metadata in metadatas
        if isinstance(metadata, TechnicalBitstreamObjectMetadata)
        and metadata.file_format == "audio/flac"
    )
    assert flac_bitstream.file_format_version == "1.2.1"

    container = next(
        metadata for metadata in metadatas
        if isinstance(metadata, TechnicalFileObjectMetadata)
    )
    assert container.file_format == "video/x-matroska"
    assert container.file_format_version == "4"
    assert container.checksum == "070822f0f55d612782ac587f9e53c37d"
    assert container.checksum_algorithm.value == "MD5"

    # Check that correct linkings are made
    assert len(container.relationships) == 2
    assert any(
        relationship for relationship in container.relationships
        if relationship.object_identifier == ffv_bitstream.object_identifier
    )
    assert any(
        relationship for relationship in container.relationships
        if relationship.object_identifier == flac_bitstream.object_identifier
    )

    # Check that streams are added into the digital object
    assert len(digital_object.streams) == 2

    audio_stream = next(
        stream for stream in digital_object.streams
        if flac_bitstream in stream.metadata
    )
    video_stream = next(
        stream for stream in digital_object.streams
        if ffv_bitstream in stream.metadata
    )

    # Each DigitalObjectStream contains a TechnicalBitstreamObjectMetadata and
    # another technical media metadata object
    # (TechnicalAudioMetadata/TechnicalVideoMetadata)
    audio_metadata = next(
        metadata for metadata in audio_stream.metadata
        if id(metadata) != id(flac_bitstream)
    )
    video_metadata = next(
        metadata for metadata in video_stream.metadata
        if id(metadata) != id(ffv_bitstream)
    )

    assert audio_metadata.codec_name == "FLAC"
    assert audio_metadata.format_version == "2.0"
    assert audio_metadata.data_rate_mode.value == "Variable"

    assert video_metadata.codec_name == "FFV1"
    assert video_metadata.sampling == "4:2:0"


@pytest.mark.parametrize(
    "grade,expected_use",
    [
        (file_scraper.defaults.BIT_LEVEL,
         "fi-dpres-file-format-identification"),
        (file_scraper.defaults.BIT_LEVEL_WITH_RECOMMENDED,
         "fi-dpres-no-file-format-validation")
    ]
)
def test_bit_level_format(monkeypatch, grade, expected_use):
    """Test metadata generation for bit level format file.

    Use attribute should be automatically set for files that are
    detected as bit-level formats.

    :param monkeypatch: Helper to conveniently monkeypatch attributes
    :param grade: Grade of scraped file
    :param expected_use: Expected value of use attribute
    """
    monkeypatch.setattr("file_scraper.scraper.Scraper.grade", lambda _: grade)
    digital_object = SIPDigitalObject(
        source_filepath="tests/data/test_file.txt",
        sip_filepath="sip_data/test_segy.sgy"
    )

    digital_object.generate_technical_metadata()
    assert digital_object.use == expected_use


def test_generate_metadata_with_predefined_values():
    """Test that it is possible to predefine values when generating metadata.
    """
    digital_object = SIPDigitalObject(
        source_filepath="tests/data/test_file.txt",
        sip_filepath="sip_data/test_file.txt"
    )

    digital_object.generate_technical_metadata(
        file_format="predefined_file_format",
        file_format_version="predefined_file_format_version",
        checksum_algorithm="SHA-256",
        checksum="predefined_checksum",
        file_created_date="predefined_file_created_date",
        object_identifier_type="predefined_object_identifier_type",
        object_identifier="predefined_object_identifier",
        charset="UTF-16",
        original_name="predefined_original_name",
        format_registry_name="predefined_format_registry_name",
        format_registry_key="predefined_format_registry_key",
        creating_application="predefined_creating_application",
        creating_application_version="predefined_creating_application_version"
    )

    metadata = [
        data for data in digital_object.metadata
        if isinstance(data, TechnicalFileObjectMetadata)
    ][0]

    assert metadata.file_format == "predefined_file_format"
    assert metadata.file_format_version == "predefined_file_format_version"
    assert metadata.checksum_algorithm.value == "SHA-256"
    assert metadata.checksum == "predefined_checksum"
    assert metadata.file_created_date == "predefined_file_created_date"
    assert metadata.object_identifier_type == (
        "predefined_object_identifier_type"
    )
    assert metadata.object_identifier == "predefined_object_identifier"
    assert metadata.charset.value == "UTF-16"
    assert metadata.original_name == "predefined_original_name"
    assert metadata.format_registry_name == "predefined_format_registry_name"
    assert metadata.format_registry_key == "predefined_format_registry_key"
    assert metadata.creating_application == "predefined_creating_application"
    assert metadata.creating_application_version == (
        "predefined_creating_application_version"
    )


@pytest.mark.parametrize(
    ("invalid_init_params", "error_message"),
    (
        (
            {"file_format_version": "1.0"},
            "Predefined file format version is given, but file format is not."
        ),
        (
            {"checksum_algorithm": "SHA-256"},
            "Predefined checksum algorithm is given, but checksum is not."
        ),
        (
            {"checksum": "12345"},
            "Predefined checksum is given, but checksum algorithm is not."
        ),
        (
            {"csv_delimiter": ","},
            "CSV specific parameters (csv_has_header, csv_delimiter, "
            "csv_record_separator, csv_quoting_character) can be used "
            "only with CSV files"
        ),
    )
)
def test_invalid_generate_metadata_params(invalid_init_params, error_message):
    """Test that invalid arguments when generating metadata raise an error."""
    digital_object = SIPDigitalObject(
        source_filepath="tests/data/test_file.txt",
        sip_filepath="sip_data/test_file.txt"
    )
    with pytest.raises(ValueError) as error:
        digital_object.generate_technical_metadata(**invalid_init_params)

    assert str(error.value) == error_message


@pytest.mark.parametrize(
    ("args", "correct_values"),
    (
        # Detects header when header row is declared to exist
        (
            {"csv_has_header": True},
            {
                "header": ["year", "brand", "model", "detail", "other"],
                "charset": "UTF-8",
                "delimiter": ",",
                "record_separator": "\r\n",
                "quoting_character": '"'
            }
        ),
        # Generates header when header row is declared not to exist
        (
            {"csv_has_header": False},
            {
                "header": [
                    "header1", "header2", "header3", "header4", "header5"
                ],
                "charset": "UTF-8",
                "delimiter": ",",
                "record_separator": "\r\n",
                "quoting_character": '"'
            }
        ),
        # Uses predefined values to override scraped values
        (
            {
                "csv_has_header": True,
                "charset": "ISO-8859-15",
                "csv_delimiter": ";",
                "csv_record_separator": "CR+LF",
                "csv_quoting_character": "'"
            },
            {
                "header": ["year,brand,model,detail,other"],
                "charset": "ISO-8859-15",
                "delimiter": ";",
                "record_separator": "CR+LF",
                "quoting_character": "'"
            }
        )
    )
)
def test_generating_technical_metadata_for_csv_file(
    args, correct_values
):
    """Test that generating technical metadata for a CSV file results in
    correct information.
    """
    digital_object = SIPDigitalObject(
        source_filepath="tests/data/test_csv.csv",
        sip_filepath="sip_data/test_csv.csv"
    )

    digital_object.generate_technical_metadata(file_format="text/csv", **args)

    # Technical object metadata
    metadata = [
        data for data in digital_object.metadata
        if isinstance(data, TechnicalFileObjectMetadata)
    ][0]
    assert metadata.file_format == "text/csv"
    assert metadata.file_format_version == "(:unap)"
    assert metadata.charset.value == correct_values["charset"]
    assert metadata.checksum_algorithm.value == "MD5"
    assert metadata.checksum == "bca595dbb4536d957f2dbabf83ceecae"
    assert metadata.original_name == "test_csv.csv"

    # File creation date cannot be tested with hardcoded time, because it will
    # differ according to when the user has cloned the repository (and created
    # the test file while doing so). Settle for testing that file creation date
    # is in ISO format
    format_string = "%Y-%m-%dT%H:%M:%S"
    # Raises error if file_created_date doesn't follow the right format
    datetime.strptime(metadata.file_created_date, format_string)

    # Technical CSV metadata
    metadata = [
        data for data in digital_object.metadata
        if isinstance(data, TechnicalCSVMetadata)
    ][0]
    assert metadata.filenames == ["sip_data/test_csv.csv"]
    assert metadata.header == correct_values["header"]
    assert metadata.charset == correct_values["charset"]
    assert metadata.delimiter == correct_values["delimiter"]
    assert metadata.record_separator == correct_values["record_separator"]
    assert metadata.quoting_character == correct_values["quoting_character"]


@pytest.mark.parametrize(
    "event_type,event_detail,event_outcome_detail,expected_linked_agents",
    [
        (
            "message digest calculation",
            "Checksum calculation for digital objects",
            "Checksum successfully calculated for digital objects.",
            {"file-scraper"}
        ),
        (
            "metadata extraction",
            "Technical metadata extraction as PREMIS metadata from "
            "digital objects",
            "PREMIS metadata successfully created from extracted technical "
            "metadata.",
            {"MagicTextScraper", "MimeMatchScraper", "ResultsMergeScraper",
             "TextEncodingMetaScraper", "TextfileScraper", "file-scraper"}
        ),
        (
            "format identification",
            "MIME type and version identification",
            "File MIME type and format version successfully identified.",
            {"FidoDetector", "MagicDetector", "ODFDetector",
             "PredefinedDetector", "SegYDetector", "SiardDetector",
             "file-scraper"}
        ),
    ]
)
def test_event(event_type, event_detail, event_outcome_detail,
               expected_linked_agents):
    """Test that PREMIS event metadata is created.

    :param event_type: Event type
    :param event_detail: Expected event detail
    :param event_event_outcome_detail: Expected event outcome detail
    :param expected_linked_agents: Names of agents that should be linked
        to event
    """
    digital_object = SIPDigitalObject(
        source_filepath="tests/data/test_file.txt",
        sip_filepath="sip_data/test_file.txt"
    )
    digital_object.generate_technical_metadata()

    event = next(
        metadata for metadata in digital_object.metadata
        if (
            isinstance(metadata, DigitalProvenanceEventMetadata)
            and metadata.event_type == event_type
        )
    )
    assert event.event_detail == event_detail
    assert event.event_outcome.value == "success"
    assert event.event_outcome_detail == event_outcome_detail
    assert event.event_identifier_type == "UUID"
    assert event.event_identifier is None

    # Expected agents should be linked to event
    linked_agents = {linked_agent.agent_metadata
                     for linked_agent in event.linked_agents}
    assert {agent.agent_name for agent in linked_agents} \
        == expected_linked_agents

    for agent in linked_agents:
        assert agent.agent_type.value == "software"
        assert agent.agent_version == file_scraper.__version__
        assert agent.agent_identifier_type == "UUID"
        assert agent.agent_identifier is None
        # TODO: currently agent_note is None for all scrapers/detectors,
        # because tools have not been defined in file-scraper!
        #
        # assert agent.agent_note.startswith('Used tools (name-version): ')

    # Expected agent metadata should have been added also to
    # digital_object
    assert expected_linked_agents <= {
        metadata.agent_name for metadata in digital_object.metadata
        if isinstance(metadata, DigitalProvenanceAgentMetadata)
    }


@pytest.mark.parametrize(
    "kwargs,expected_event_types",
    [
        # No arguments, all events should be created
        (
            {},
            {"metadata extraction", "format identification",
             "message digest calculation"}
        ),
        # Checksum is predefined, so it should not be calculated
        (
            {"checksum": "1234", "checksum_algorithm": "MD5"},
            {"metadata extraction", "format identification"}
        ),
        # File format is predefined, so it should not be identified
        (
            {"file_format": "text/plain"},
            {"metadata extraction", "message digest calculation"}
        )

    ]
)
def test_skip_event(kwargs, expected_event_types):
    """Test that unnecessary events are not created.

    :param kwargs: Arguments for metadata generation
    :param expected_event_types: Types of events that should be created
    """
    digital_object = SIPDigitalObject(
        source_filepath="tests/data/test_file.txt",
        sip_filepath="sip_data/test_file.txt"
    )
    digital_object.generate_technical_metadata(**kwargs)
    event_types = {
        metadata.event_type for metadata in digital_object.metadata
        if isinstance(metadata, DigitalProvenanceEventMetadata)
    }
    assert event_types == expected_event_types
