"""Module for handling digital objects in SIP."""
from pathlib import Path
from typing import Iterable, Optional, Union

import mets_builder


class SIPDigitalObject(mets_builder.DigitalObject):
    """Class for handling digital objects in SIPs.

    This class inherits DigitalObject of mets_builder, meaning that it can be
    used normally in METS building, for example by adding it to a structural
    map. In addition, it provides functionality for handling digital objects in
    the SIP context.
    """

    def __init__(
        self,
        source_filepath: Union[str, Path],
        sip_filepath: Union[str, Path],
        metadata: Optional[Iterable[mets_builder.metadata.MetadataBase]] = (
            None
        ),
        streams: Optional[Iterable[mets_builder.DigitalObjectStream]] = None,
        identifier: Optional[str] = None,
        *args,
        **kwargs
    ) -> None:
        """Constructor for SIPDigitalObject.

        :param source_filepath: File path of the local source file for this
            digital object. Symbolic links in the path are resolved.
        :param sip_filepath: File path of this digital object in the
            SIP, relative to the SIP root directory. Note that this can be
            different than the path in the local filesystem.
        :param metadata: Iterable of metadata objects that describe this
            stream. Note that the metadata should be administrative metadata,
            and any descriptive metadata of a digital object should be added to
            a div in a structural map.
        :param streams: Iterable of DigitalObjectStreams, representing the
            streams of this digital object.
        :param str identifier: Identifier for the digital object. The
            identifier must be unique in the METS document. If None, the
            identifier is generated automatically.
        """
        self.source_filepath = Path(source_filepath)

        super().__init__(
            sip_filepath=sip_filepath,
            metadata=metadata,
            streams=streams,
            identifier=identifier,
            *args,
            **kwargs
        )

    @property
    def source_filepath(self) -> Path:
        """Getter for source_filepath."""
        return self._source_filepath

    @source_filepath.setter
    def source_filepath(self, source_filepath):
        """Setter for source_filepath."""
        source_filepath = Path(source_filepath)

        # Resolve symbolic links in path
        source_filepath = source_filepath.resolve()

        if not source_filepath.is_file():
            raise ValueError(
                f"Source filepath '{source_filepath}' for the digital object "
                "is not a file."
            )

        self._source_filepath = source_filepath
