"""Module for handling digital objects in SIP."""
import platform
from datetime import datetime
from pathlib import Path
from typing import Iterable, Optional, Union

import mets_builder
from file_scraper.scraper import Scraper
from mets_builder.defaults import UNAV


def _generate_metadata_argument_validation(
    ovr_file_format,
    ovr_file_format_version,
    ovr_checksum_algorithm,
    ovr_checksum
):
    """Validata arguments given to generate_technical_metadata method."""
    if ovr_file_format and not ovr_file_format_version:
        raise ValueError(
            "Overriding file format is given, but file format version is "
            "not."
        )
    if ovr_file_format_version and not ovr_file_format:
        raise ValueError(
            "Overriding file format version is given, but file format is "
            "not."
        )
    if ovr_checksum_algorithm and not ovr_checksum:
        raise ValueError(
            "Overriding checksum algorithm is given, but checksum is not."
        )
    if ovr_checksum and not ovr_checksum_algorithm:
        raise ValueError(
            "Overriding checksum is given, but checksum algorithm is not."
        )


def _file_creation_date(filepath: Path) -> str:
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


def _create_technical_image_metadata(
    stream: dict
) -> mets_builder.metadata.TechnicalImageMetadata:
    """Create technical image metadata object from file-scraper stream."""
    return mets_builder.metadata.TechnicalImageMetadata(
        compression=stream["compression"],
        colorspace=stream["colorspace"],
        width=stream["width"],
        height=stream["height"],
        bps_value=stream["bps_value"],
        bps_unit=stream["bps_unit"],
        samples_per_pixel=stream["samples_per_pixel"],
        mimetype=stream.get("mimetype", None),
        byte_order=stream.get("byte_order", None),
        icc_profile_name=stream.get("icc_profile_name", None)
    )


def _create_technical_audio_metadata(
    stream: dict
) -> mets_builder.metadata.TechnicalAudioMetadata:
    """Create technical audio metadata from file-scraper stream."""
    return mets_builder.metadata.TechnicalAudioMetadata(
        codec_quality=stream["codec_quality"],
        data_rate_mode=stream["data_rate_mode"],
        audio_data_encoding=stream.get("audio_data_encoding", UNAV),
        bits_per_sample=stream.get("bits_per_sample", "0"),
        codec_creator_app=stream.get("codec_creator_app", UNAV),
        codec_creator_app_version=stream.get(
            "codec_creator_app_version", UNAV
        ),
        codec_name=stream.get("codec_name", UNAV),
        data_rate=stream.get("data_rate", "0"),
        sampling_frequency=stream.get("sampling_frequency", "0"),
        duration=stream.get("duration", UNAV),
        num_channels=stream.get("num_channels", UNAV)
    )


def _create_technical_video_metadata(
    stream: dict
) -> mets_builder.metadata.TechnicalVideoMetadata:
    """Create technical video metadata from file-scraper stream."""
    return mets_builder.metadata.TechnicalVideoMetadata(
        duration=stream.get("duration", UNAV),
        data_rate=stream.get("data_rate", "0"),
        bits_per_sample=stream.get("bits_per_sample", "0"),
        color=stream["color"],
        codec_creator_app=stream.get("codec_creator_app", UNAV),
        codec_creator_app_version=stream.get(
            "codec_creator_app_version", UNAV
        ),
        codec_name=stream.get("codec_name", UNAV),
        codec_quality=stream["codec_quality"],
        data_rate_mode=stream["data_rate_mode"],
        frame_rate=stream.get("frame_rate", "0"),
        pixels_horizontal=stream.get("width", "0"),
        pixels_vertical=stream.get("height", "0"),
        par=stream.get("par", "0"),
        dar=stream.get("dar", UNAV),
        sampling=stream.get("sampling", UNAV),
        signal_format=stream.get("signal_format", UNAV),
        sound=stream["sound"]
    )


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

    def _create_technical_object_metadata(
        self,
        scraper: Scraper,
        stream: dict,
        ovr_file_format: Optional[str] = None,
        ovr_file_format_version: Optional[str] = None,
        ovr_checksum_algorithm: Union[
            mets_builder.metadata.ChecksumAlgorithm, str, None
        ] = None,
        ovr_checksum: Optional[str] = None,
        ovr_file_created_date: Optional[str] = None,
        ovr_object_identifier_type: Optional[str] = None,
        ovr_object_identifier: Optional[str] = None,
        ovr_charset: Union[mets_builder.metadata.Charset, str, None] = None,
        ovr_original_name: Optional[str] = None,
        format_registry_name: Optional[str] = None,
        format_registry_key: Optional[str] = None,
        creating_application: Optional[str] = None,
        creating_application_version: Optional[str] = None
    ) -> mets_builder.metadata.TechnicalObjectMetadata:
        """Create technical object metadata object from file-scraper scraper
        and stream.
        """
        def _first(*priority_order):
            """Return the first given value that is not None.

            If all values are None, return None.
            """
            return next(
                (value for value in priority_order if value is not None),
                None
            )

        return mets_builder.metadata.TechnicalObjectMetadata(
            file_format=_first(ovr_file_format, scraper.mimetype),
            file_format_version=_first(
                ovr_file_format_version, scraper.version
            ),
            checksum_algorithm=_first(ovr_checksum_algorithm, "MD5"),
            checksum=_first(ovr_checksum, scraper.checksum(algorithm="MD5")),
            file_created_date=_first(
                ovr_file_created_date,
                _file_creation_date(self.source_filepath)
            ),
            object_identifier_type=ovr_object_identifier_type,
            object_identifier=ovr_object_identifier,
            charset=_first(ovr_charset, stream.get("charset", None)),
            original_name=_first(ovr_original_name, self.source_filepath.name),
            format_registry_name=format_registry_name,
            format_registry_key=format_registry_key,
            creating_application=creating_application,
            creating_application_version=creating_application_version
        )

    def generate_technical_metadata(
        self,
        ovr_file_format: Optional[str] = None,
        ovr_file_format_version: Optional[str] = None,
        ovr_checksum_algorithm: Union[
            mets_builder.metadata.ChecksumAlgorithm, str, None
        ] = None,
        ovr_checksum: Optional[str] = None,
        ovr_file_created_date: Optional[str] = None,
        ovr_object_identifier_type: Optional[str] = None,
        ovr_object_identifier: Optional[str] = None,
        ovr_charset: Union[mets_builder.metadata.Charset, str, None] = None,
        ovr_original_name: Optional[str] = None,
        format_registry_name: Optional[str] = None,
        format_registry_key: Optional[str] = None,
        creating_application: Optional[str] = None,
        creating_application_version: Optional[str] = None,
    ) -> None:
        """Generate technical object metadata for this digital object.

        Scrapes the file found in SIPDigitalObject.source_filepath, turning the
        scraped information into a
        mets_builder.metadata.TechnicalObjectMetadata object, and finally adds
        the metadata to this digital object.

        The metadata is overridden or enriched with the user-given values,
        whenever provided. It is possible, however, to provide no overriding
        values at all and use only scraped values.

        For image, audio and video files also corresponding file type specific
        technical metadata object is created and added to the digital object.

        :param ovr_file_format: Overrides scraped file format of the object.
            Mimetype of the file, e.g. 'image/tiff'. When set,
            ovr_file_format_version has to be set as well.
        :param ovr_file_format_version: Overrides scraped file format version
            of the object. Version number of the file format, e.g. '1.2'. When
            set, ovr_file_format has to be set as well.
        :param ovr_checksum_algorithm: Overrides scraped checksum algorithm of
            the object. The specific algorithm used to construct the checksum
            for the digital object. If given as string, the value is cast to
            mets_builder.metadata.ChecksumAlgorithm and results in error if it
            is not a valid checksum algorithm. The allowed values can be found
            from ChecksumAlgorithm documentation. When set, ovr_checksum has to
            be set as well.
        :param ovr_checksum: Overrides scraped checksum of the object. The
            output of the message digest algorithm. When set,
            ovr_checksum_algorithm has to be set as well.
        :param ovr_file_created_date: Overrides scraped file created date of
            the object. The actual or approximate date and time the object was
            created. The time information must be expressed using either the
            ISO-8601 format, or its extended version ISO_8601-2.
        :param ovr_object_identifier_type: Overrides generated object
            identifier type of the object. Standardized identifier types should
            be used when possible (e.g., an ISBN for books). When set,
            ovr_object_identifier has to be set as well.
        :param ovr_object_identifier: Overrides generated object identifier of
            the object. File identifiers should be globally unique. When set,
            ovr_object_identifier_type has to be set as well.
        :param ovr_charset: Overrides scraped charset of the object. Character
            encoding of the file. If given as string, the value is cast to
            mets_builder.metadata.Charset and results in error if it is not a
            valid charset. The allowed values can be found from Charset
            documentation.
        :param ovr_original_name: Overrides scraped original name of the
            object.
        :param format_registry_name: Enriches generated metadata with format
            registry name. Name identifying a format registry, if a format
            registry is used to give further information about the file format.
            When set, format_registry_key has to be set as well.
        :param format_registry_key: Enriches generated metadata with format
            registry key. The unique key used to reference an entry for this
            file format in a format registry. When set, format_registry_name
            has to be set as well.
        :param creating_application: Enriches generated metadata with creating
            application. Software that was used to create this file. When set,
            creating_application_version has to be set as well.
        :param creating_application_version: Enriches generated metadata with
            creating application version. Version of the software that was
            used to create this file. When set, creating_application has to be
            set as well.
        """
        if self._technical_metadata_generated:
            raise MetadataGenerationError(
                "Technical metadata has already been generated for the "
                "digital object."
            )

        _generate_metadata_argument_validation(
            ovr_file_format,
            ovr_file_format_version,
            ovr_checksum_algorithm,
            ovr_checksum
        )

        scraper = Scraper(
            filename=str(self.source_filepath),
            mimetype=ovr_file_format,
            version=ovr_file_format_version,
            charset=ovr_charset
        )
        scraper.scrape(check_wellformed=False)
        # TODO: Handle streams, do not assume object has only one stream
        stream = scraper.streams[0]

        metadata = self._create_technical_object_metadata(
            scraper,
            stream,
            ovr_file_format=ovr_file_format,
            ovr_file_format_version=ovr_file_format_version,
            ovr_checksum_algorithm=ovr_checksum_algorithm,
            ovr_checksum=ovr_checksum,
            ovr_file_created_date=ovr_file_created_date,
            ovr_object_identifier_type=ovr_object_identifier_type,
            ovr_object_identifier=ovr_object_identifier,
            ovr_charset=ovr_charset,
            ovr_original_name=ovr_original_name,
            format_registry_name=format_registry_name,
            format_registry_key=format_registry_key,
            creating_application=creating_application,
            creating_application_version=creating_application_version
        )
        self.add_metadata(metadata)

        if stream["stream_type"] == "image":
            metadata = _create_technical_image_metadata(stream)
            self.add_metadata(metadata)
        if stream["stream_type"] == "audio":
            metadata = _create_technical_audio_metadata(stream)
            self.add_metadata(metadata)
        if stream["stream_type"] == "video":
            metadata = _create_technical_video_metadata(stream)
            self.add_metadata(metadata)

        self._technical_metadata_generated = True
