"""Test SIPDigitalObject."""
import pytest

from siptools_ng.sip_digital_object import SIPDigitalObject


def test_digital_object_source_file_exists():
    """Test that nonexistent source file raises error."""
    with pytest.raises(ValueError) as error:
        SIPDigitalObject(
            source_filepath="tests/data/nonexistent_test_file.txt",
            sip_filepath="sip_data/test_file.txt"
        )
    assert str(error.value) == (
        "Source file 'tests/data/nonexistent_test_file.txt' for the digital "
        "object does not exist."
    )
