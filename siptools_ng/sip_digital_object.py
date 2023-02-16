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
            digital object.
        :type source_filepath: Union[str, Path]
        :param sip_filepath: File path of this digital object in the
            SIP, relative to the SIP root directory. Note that this can be
            different than the path in the local filesystem.
        :type sip_filepath: Union[str, Path]
        :param metadata: Iterable of metadata objects that describe this
            stream. Note that the metadata should be administrative metadata,
            and any descriptive metadata of a digital object should be added to
            a div in a structural map.
        :type metadata: Iterable[MetadataBase], optional
        :param streams: Iterable of DigitalObjectStreams, representing the
            streams of this digital object.
        :type streams: Iterable[DigitalObjectStream], optional
        :param str identifier: Identifier for the digital object. The
            identifier must be unique in the METS document. If None, the
            identifier is generated automatically.
        :type identifier: str, optional

        """
        self.source_filepath = Path(source_filepath)
        if not self.source_filepath.is_file():
            raise ValueError(
                f"Source filepath '{source_filepath}' for the digital object "
                "is not a file."
            )

        super().__init__(
            sip_filepath=sip_filepath,
            metadata=metadata,
            streams=streams,
            identifier=identifier,
            *args,
            **kwargs
        )
