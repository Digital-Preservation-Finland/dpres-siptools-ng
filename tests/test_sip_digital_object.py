"""Test SIPDigitalObject."""
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
    assert str(error.value) == (
        f"Source filepath '{source_filepath}' for the digital object is not a "
        "file."
    )
