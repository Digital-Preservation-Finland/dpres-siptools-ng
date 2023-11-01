"""Test SIPDigitalObject."""
from datetime import datetime

import pytest
from mets_builder.metadata import (TechnicalAudioMetadata,
                                   TechnicalImageMetadata,
                                   TechnicalObjectMetadata,
                                   TechnicalVideoMetadata)

from siptools_ng.sip_digital_object import (MetadataGenerationError,
                                            SIPDigitalObject)


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

    assert len(digital_object.metadata) == 1
    metadata = digital_object.metadata.pop()

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

    assert len(digital_object.metadata) == 2

    # Technical object metadata
    metadata = [
        data for data in digital_object.metadata
        if isinstance(data, TechnicalObjectMetadata)
    ][0]
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

    # Technical image metadata
    metadata = [
        data for data in digital_object.metadata
        if isinstance(data, TechnicalImageMetadata)
    ][0]
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
    """Test that generating technical metadata for an audioo file results in
    correct information.
    """
    digital_object = SIPDigitalObject(
        source_filepath="tests/data/test_audio.wav",
        sip_filepath="sip_data/test_audio.wav"
    )

    digital_object.generate_technical_metadata()

    assert len(digital_object.metadata) == 2

    # Technical object metadata
    metadata = [
        data for data in digital_object.metadata
        if isinstance(data, TechnicalObjectMetadata)
    ][0]
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

    # Technical audio metadata
    metadata = [
        data for data in digital_object.metadata
        if isinstance(data, TechnicalAudioMetadata)
    ][0]
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

    assert len(digital_object.metadata) == 2

    # Technical object metadata
    metadata = [
        data for data in digital_object.metadata
        if isinstance(data, TechnicalObjectMetadata)
    ][0]
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
