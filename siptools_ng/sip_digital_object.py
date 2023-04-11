"""Module for handling digital objects in SIP."""
import platform
from datetime import datetime
from pathlib import Path
from typing import Iterable, Optional, Union

import mets_builder
from file_scraper.scraper import Scraper


class MetadataGenerationError(Exception):
    """Error raised when there is an error in metadata generation."""


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
        self._technical_metadata_generated = False

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

    def _file_creation_date(self, filepath: Path) -> str:
        """Return creation date for file.

        Try to get the date that a file was created, falling back to when it
        was last modified if that isn't possible. See
        http://stackoverflow.com/a/39501288/1709587 for explanation.

        :param filepath: Path to the file.

        :returns: Timestamp for the creation date of the file, or for the last
            modification date if the creation date is not found.
        """
        stat = filepath.stat()

        if platform.system() == "Windows":
            creation_date = datetime.fromtimestamp(stat.st_ctime)
        else:
            try:
                # Some Unix systems such as macOS might have birthtime defined
                creation_date = datetime.fromtimestamp(
                    stat.st_birthtime  # type:ignore
                )
            except AttributeError:
                # We're probably on Linux. No easy way to get creation dates
                # here, so we'll settle for when its content was last modified.
                creation_date = datetime.fromtimestamp(stat.st_mtime)

        return creation_date.isoformat(timespec="seconds")

    def generate_technical_metadata(self) -> None:
        """Generate technical object metadata for this digital object.

        Scrapes the file found in SIPDigitalObject.source_filepath, turning the
        scraped information into a
        mets_builder.metadata.TechnicalObjectMetadata object, and finally adds
        the metadata to this digital object.
        """
        if self._technical_metadata_generated:
            raise MetadataGenerationError(
                "Technical metadata has already been generated for the "
                "digital object."
            )

        scraper = Scraper(filename=str(self.source_filepath))
        scraper.scrape(check_wellformed=False)
        # TODO: Handle streams, do not assume object has only one stream
        stream = scraper.streams[0]

        technical_metadata = mets_builder.metadata.TechnicalObjectMetadata(
            file_format=scraper.mimetype,
            file_format_version=scraper.version,
            checksum_algorithm="MD5",
            checksum=scraper.checksum(algorithm="MD5"),
            file_created_date=self._file_creation_date(self.source_filepath),
            charset=stream.get("charset", None),
            original_name=self.source_filepath.name
        )

        self.add_metadata(technical_metadata)
        self._technical_metadata_generated = True
