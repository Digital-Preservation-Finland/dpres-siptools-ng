"""Test SIPDigitalObject."""
from datetime import datetime

import pytest

from siptools_ng.sip_digital_object import SIPDigitalObject


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

    assert len(digital_object.metadata) == 1
    metadata = digital_object.metadata.pop()

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
