"""Module for handling digital objects in SIP."""
import platform
from datetime import datetime
from pathlib import Path
from typing import Iterable, Optional, Union

import mets_builder
from file_scraper.scraper import Scraper
from mets_builder.defaults import UNAV

from siptools_ng import digital_provenance


def _first(*priority_order):
    """Return the first given value that is not None.

    If all values are None, return None.
    """
    return next(
        (value for value in priority_order if value is not None),
        None
    )


def _normalize_unav(value):
    """
    Normalize value to "0" if the value is "(:unav)", otherwise return the
    value as-is
    """
    if value == UNAV:
        return "0"

    return value


def _create_technical_media_metadata(stream: dict) -> \
        Optional[mets_builder.metadata.TechnicalObjectMetadata]:
    """
    Generate technical media metadata for a stream if applicable
    (eg. AudioMD for audio streams, MixMD for image and VideoMD for video).

    :param stream: Individual stream metadata as returned by file-scraper
    """
    stream_type = stream["stream_type"]
    if stream_type == "image":
        return _create_technical_image_metadata(stream)
    if stream_type == "audio":
        return _create_technical_audio_metadata(stream)
    if stream_type == "video":
        return _create_technical_video_metadata(stream)

    return None


def _generate_metadata_argument_validation(
    predef_file_format,
    predef_file_format_version,
    predef_checksum_algorithm,
    predef_checksum
):
    """Validata arguments given to generate_technical_metadata method."""
    if predef_file_format and not predef_file_format_version:
        raise ValueError(
            "Predefined file format is given, but file format version is "
            "not."
        )
    if predef_file_format_version and not predef_file_format:
        raise ValueError(
            "Predefined file format version is given, but file format is "
            "not."
        )
    if predef_checksum_algorithm and not predef_checksum:
        raise ValueError(
            "Predefined checksum algorithm is given, but checksum is not."
        )
    if predef_checksum and not predef_checksum_algorithm:
        raise ValueError(
            "Predefined checksum is given, but checksum algorithm is not."
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
        bits_per_sample=_normalize_unav(stream.get("bits_per_sample", "0")),
        codec_creator_app=stream.get("codec_creator_app", UNAV),
        codec_creator_app_version=stream.get(
            "codec_creator_app_version", UNAV
        ),
        codec_name=stream.get("codec_name", UNAV),
        data_rate=_normalize_unav(stream.get("data_rate", "0")),
        sampling_frequency=_normalize_unav(
            stream.get("sampling_frequency", "0")
        ),
        duration=stream.get("duration", UNAV),
        num_channels=stream.get("num_channels", UNAV)
    )


def _create_technical_video_metadata(
    stream: dict
) -> mets_builder.metadata.TechnicalVideoMetadata:
    """Create technical video metadata from file-scraper stream."""
    return mets_builder.metadata.TechnicalVideoMetadata(
        duration=stream.get("duration", UNAV),
        data_rate=_normalize_unav(stream.get("data_rate", "0")),
        bits_per_sample=_normalize_unav(stream.get("bits_per_sample", "0")),
        color=stream["color"],
        codec_creator_app=stream.get("codec_creator_app", UNAV),
        codec_creator_app_version=stream.get(
            "codec_creator_app_version", UNAV
        ),
        codec_name=stream.get("codec_name", UNAV),
        codec_quality=stream["codec_quality"],
        data_rate_mode=stream["data_rate_mode"],
        frame_rate=_normalize_unav(stream.get("frame_rate", "0")),
        pixels_horizontal=_normalize_unav(stream.get("width", "0")),
        pixels_vertical=_normalize_unav(stream.get("height", "0")),
        par=_normalize_unav(stream.get("par", "0")),
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
        :param identifier: Identifier for the digital object. The
            identifier must be unique in the METS document. If None, the
            identifier is generated automatically.
        """
        self.source_filepath = Path(source_filepath)
        self._technical_metadata_generated = False
        self._scrape_cache = None

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

    def _scrape_file(
        self, mimetype=None, version=None, charset=None
    ) -> Scraper:
        """Scrape file using file-scraper.

        When the scraping is done, the scraper is cached for later use. If
        cached scraper is found, the cached scraper is returned and scraping is
        skipped.
        """
        if self._scrape_cache:
            return self._scrape_cache

        scraper = Scraper(
            filename=str(self.source_filepath),
            mimetype=mimetype,
            version=version,
            charset=charset
        )
        scraper.scrape(check_wellformed=False)
        self._scrape_cache = scraper

        return scraper

    def _create_technical_file_object_metadata(
        self,
        scraper: Scraper,
        stream: dict,
        predef_file_format: Optional[str] = None,
        predef_file_format_version: Optional[str] = None,
        predef_checksum_algorithm: Union[
            mets_builder.metadata.ChecksumAlgorithm, str, None
        ] = None,
        predef_checksum: Optional[str] = None,
        predef_file_created_date: Optional[str] = None,
        predef_object_identifier_type: Optional[str] = None,
        predef_object_identifier: Optional[str] = None,
        predef_charset: Union[mets_builder.metadata.Charset, str, None] = None,
        predef_original_name: Optional[str] = None,
        format_registry_name: Optional[str] = None,
        format_registry_key: Optional[str] = None,
        creating_application: Optional[str] = None,
        creating_application_version: Optional[str] = None
    ) -> mets_builder.metadata.TechnicalFileObjectMetadata:
        """Create technical object metadata object from file-scraper scraper
        and stream.
        """
        return mets_builder.metadata.TechnicalFileObjectMetadata(
            file_format=_first(predef_file_format, scraper.mimetype),
            file_format_version=_first(
                predef_file_format_version, scraper.version
            ),
            checksum_algorithm=_first(predef_checksum_algorithm, "MD5"),
            checksum=_first(
                predef_checksum, scraper.checksum(algorithm="MD5")
            ),
            file_created_date=_first(
                predef_file_created_date,
                _file_creation_date(self.source_filepath)
            ),
            object_identifier_type=predef_object_identifier_type,
            object_identifier=predef_object_identifier,
            charset=_first(predef_charset, stream.get("charset", None)),
            original_name=_first(
                predef_original_name, self.source_filepath.name
            ),
            format_registry_name=format_registry_name,
            format_registry_key=format_registry_key,
            creating_application=creating_application,
            creating_application_version=creating_application_version
        )

    def _generate_technical_metadata(
        self,
        predef_file_format: Optional[str] = None,
        predef_file_format_version: Optional[str] = None,
        predef_checksum_algorithm: Union[
            mets_builder.metadata.ChecksumAlgorithm, str, None
        ] = None,
        predef_checksum: Optional[str] = None,
        predef_file_created_date: Optional[str] = None,
        predef_object_identifier_type: Optional[str] = None,
        predef_object_identifier: Optional[str] = None,
        predef_charset: Union[mets_builder.metadata.Charset, str, None] = None,
        predef_original_name: Optional[str] = None,
        format_registry_name: Optional[str] = None,
        format_registry_key: Optional[str] = None,
        creating_application: Optional[str] = None,
        creating_application_version: Optional[str] = None,
    ):
        """Generate technical metadata for digital objects.

        See the public corresponding method generate_technical_metadata for
        more documentation.
        """
        if self._technical_metadata_generated:
            raise MetadataGenerationError(
                "Technical metadata has already been generated for the "
                "digital object."
            )

        _generate_metadata_argument_validation(
            predef_file_format,
            predef_file_format_version,
            predef_checksum_algorithm,
            predef_checksum
        )

        scraper = self._scrape_file(
            mimetype=predef_file_format,
            version=predef_file_format_version,
            charset=predef_charset
        )
        stream = scraper.streams[0]

        container_metadata = self._create_technical_file_object_metadata(
            scraper,
            stream,
            predef_file_format=predef_file_format,
            predef_file_format_version=predef_file_format_version,
            predef_checksum_algorithm=predef_checksum_algorithm,
            predef_checksum=predef_checksum,
            predef_file_created_date=predef_file_created_date,
            predef_object_identifier_type=predef_object_identifier_type,
            predef_object_identifier=predef_object_identifier,
            predef_charset=predef_charset,
            predef_original_name=predef_original_name,
            format_registry_name=format_registry_name,
            format_registry_key=format_registry_key,
            creating_application=creating_application,
            creating_application_version=creating_application_version
        )
        self.add_metadata(container_metadata)

        # Create media metadata (eg. AudioMD, MixMD, VideoMD)
        media_metadata = _create_technical_media_metadata(stream)
        if media_metadata:
            self.add_metadata(media_metadata)

        if len(scraper.streams) > 1:
            # Image or video container, add streams
            self._add_streams(
                scraper.streams, file_metadata=container_metadata
            )

        # Create digital provenance
        if not predef_checksum:
            digital_provenance.add_checksum_calculation_event(self)

        self._technical_metadata_generated = True

    def generate_technical_metadata(
        self,
        predef_file_format: Optional[str] = None,
        predef_file_format_version: Optional[str] = None,
        predef_checksum_algorithm: Union[
            mets_builder.metadata.ChecksumAlgorithm, str, None
        ] = None,
        predef_checksum: Optional[str] = None,
        predef_file_created_date: Optional[str] = None,
        predef_object_identifier_type: Optional[str] = None,
        predef_object_identifier: Optional[str] = None,
        predef_charset: Union[mets_builder.metadata.Charset, str, None] = None,
        predef_original_name: Optional[str] = None,
        format_registry_name: Optional[str] = None,
        format_registry_key: Optional[str] = None,
        creating_application: Optional[str] = None,
        creating_application_version: Optional[str] = None,
    ) -> None:
        """Generate technical metadata for this digital object.

        CSV files are impossible to differentiate from other text files
        with certainty using only programmatic methods. For this reason the
        specialized method generate_technical_csv_metadata should be used
        instead of this one when generating technical metadata for CSV files.

        Scrapes the file found in SIPDigitalObject.source_filepath, turning the
        scraped information into a
        mets_builder.metadata.TechnicalFileObjectMetadata object, and finally
        adds the metadata to this digital object.

        The metadata is overridden or enriched with the user-given predefined
        values, whenever provided. It is possible, however, to provide no
        predefined values at all and use only scraped values.

        For image, audio and video files also corresponding file type specific
        technical metadata object is created and added to the digital object.

        :param predef_file_format: Overrides scraped file format of the object
            with a predefined value. Mimetype of the file, e.g. 'image/tiff'.
            When set, predef_file_format_version has to be set as well.
        :param predef_file_format_version: Overrides scraped file format
            version of the object with a predefined value. Version number of
            the file format, e.g. '1.2'. When set, predef_file_format has to be
            set as well.
        :param predef_checksum_algorithm: Overrides scraped checksum algorithm
            of the object with a predefined value. The specific algorithm used
            to construct the checksum for the digital object. If given as
            string, the value is cast to
            mets_builder.metadata.ChecksumAlgorithm and results in error if it
            is not a valid checksum algorithm. The allowed values can be found
            from ChecksumAlgorithm documentation. When set, predef_checksum has
            to be set as well.
        :param predef_checksum: Overrides scraped checksum of the object with a
            predefined value. The output of the message digest algorithm. When
            set, predef_checksum_algorithm has to be set as well.
        :param predef_file_created_date: Overrides scraped file created date of
            the object with a predefined value. The actual or approximate date
            and time the object was created. The time information must be
            expressed using either the ISO-8601 format, or its extended version
            ISO_8601-2.
        :param predef_object_identifier_type: Overrides generated object
            identifier type of the object with a predefined value. Standardized
            identifier types should be used when possible (e.g., an ISBN for
            books). When set, predef_object_identifier has to be set as well.
        :param predef_object_identifier: Overrides generated object identifier
            of the object with a predefined value. File identifiers should be
            globally unique. When set, predef_object_identifier_type has to be
            set as well.
        :param predef_charset: Overrides scraped charset of the object with a
            predefined value. Character encoding of the file. If given as
            string, the value is cast to mets_builder.metadata.Charset and
            results in error if it is not a valid charset. The allowed values
            can be found from Charset documentation.
        :param predef_original_name: Overrides scraped original name of the
            object with a predefined value.
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
        if predef_file_format == "text/csv":
            raise ValueError(
                "Given predef_file_format is 'text/csv'. Use specialized "
                "method generate_technical_csv_metadata to generate metadata "
                "for CSV files."
            )

        self._generate_technical_metadata(
            predef_file_format=predef_file_format,
            predef_file_format_version=predef_file_format_version,
            predef_checksum_algorithm=predef_checksum_algorithm,
            predef_checksum=predef_checksum,
            predef_file_created_date=predef_file_created_date,
            predef_object_identifier_type=predef_object_identifier_type,
            predef_object_identifier=predef_object_identifier,
            predef_charset=predef_charset,
            predef_original_name=predef_original_name,
            format_registry_name=format_registry_name,
            format_registry_key=format_registry_key,
            creating_application=creating_application,
            creating_application_version=creating_application_version
        )

    def generate_technical_csv_metadata(
        self,
        has_header: bool,
        predef_delimiter: Optional[str] = None,
        predef_record_separator: Optional[str] = None,
        predef_quoting_character: Optional[str] = None,
        **kwargs
    ) -> None:
        """Generate technical metadata for this digital object.

        Using this method makes sense only for CSV files. For other types of
        files, the more generic generate_technical_metadata method should be
        used.

        This method calls generate_technical_metadata method under the hood for
        creating the more generic technical object metadata. Any keyword
        arguments that can be given to generate_technical_metadata can also be
        given here, except for predef_file_format and
        predef_file_format_version, which are set automatically to "text/csv"
        and "(:unap)". See generate_technical_metadata documentation for
        description what the method does, as well as the available parameters
        and their descriptions.

        In addition, this method creates CSV specific technical metadata object
        mets_builder.metadata.TechnicalCSVMetadata, and adds it to this
        digital object. The generated metadata is overridden with the
        user-given predefined values, whenever provided. It is possible,
        however, to provide no predefined values at all and use only scraped
        values.

        :param has_header: A boolean indicating whether this CSV file has a
            header row or not. If set as True, the first row of the file is
            used as header information. If set as False, the header metadata is
            set as "header1", "header2", etc. according to the number of fields
            in a row.
        :param predef_delimiter: Overrides the scraped delimiter character(s)
            with a predefined value. The character or combination of characters
            that are used to separate fields in the CSV file.
        :param predef_record_separator: Overrides the scraped record separator
            character(s) with a predefined value. The character or combination
            of characters that are used to separate records in the CSV file.
        :param predef_quoting_character: Overrides the scraped quoting
            character with a predefined value. The character that is used to
            encapsulate values in the CSV file. Encapsulated values can
            include characters that are otherwise treated in a special way,
            such as the delimiter character.
        """
        # Generate PREMIS:OBJECT metadata with the generic method
        self._generate_technical_metadata(
            predef_file_format="text/csv",
            predef_file_format_version="(:unap)",
            **kwargs
        )

        # Generate technical CSV metadata (ADDML)
        scraper = self._scrape_file(
            mimetype="text/csv",
            version="(:unap)",
            charset=kwargs.get("predef_charset")
        )

        # For CSV files, a single stream can be assumed
        stream = scraper.streams[0]

        # Generate header information
        first_line = stream["first_line"]
        if has_header:
            header = first_line
        else:
            header = [f"header{n}" for n in range(1, len(first_line) + 1)]

        # Create metadata
        metadata = mets_builder.metadata.TechnicalCSVMetadata(
            filenames=[self.sip_filepath],
            header=header,
            charset=_first(kwargs.get("predef_charset"), stream["charset"]),
            delimiter=_first(predef_delimiter, stream["delimiter"]),
            record_separator=_first(
                predef_record_separator, stream["separator"]
            ),
            quoting_character=_first(
                predef_quoting_character, stream["quotechar"]
            )
        )

        self.add_metadata(metadata)

    def _add_streams(
            self,
            streams: Iterable[dict],
            file_metadata: mets_builder.metadata.TechnicalFileObjectMetadata
    ) -> None:
        """
        Create PREMIS elements for the streams of a given file
        """
        for i, stream in enumerate(streams.values()):
            if i == 0:
                # Skip the container itself
                continue

            stream_metadata = \
                mets_builder.metadata.TechnicalBitstreamObjectMetadata(
                    file_format=stream["mimetype"],
                    file_format_version=stream["version"]
                )

            file_metadata.add_relationship(
                stream_metadata,
                relationship_type="structural",
                relationship_subtype="includes"
            )

            metadatas = [stream_metadata]

            # Generate video/audio metadata if applicable
            media_metadata = _create_technical_media_metadata(stream)
            if media_metadata:
                metadatas.append(media_metadata)

            # Add digital object streams
            digital_object_stream = mets_builder.DigitalObjectStream(
                # This is a list of metadata objects, not a single metadata
                # object
                metadata=metadatas
            )

            self.add_stream(digital_object_stream)
