"""Common utility functions for tests."""
from typing import Union

from mets_builder.metadata import Metadata
from mets_builder.digital_object import DigitalObject
from mets_builder.structural_map import StructuralMapDiv

from siptools_ng.file import File


def find_metadata(
    metadata_container: Union[DigitalObject, StructuralMapDiv],
    metadata_type: Metadata
) -> Metadata:
    """Get metadata of a given type from digital object or structural map div.

    :param metadata_container: Digital object or structural map div to check.
    :param metadata_type: Metadata type to check for.
    :returns: Metadata that corresponds to the metadata_type.
    """
    if isinstance(metadata_container, File):
        metadata = metadata_container.digital_object.metadata
    elif isinstance(metadata_container, StructuralMapDiv):
        metadata = metadata_container.metadata

    matching_metadata = [
        data for data in metadata
        if isinstance(data, metadata_type)
    ][0]
    return matching_metadata
