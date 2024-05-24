"""Module for handling digital objects in SIP."""
import platform
from datetime import datetime
from pathlib import Path
from typing import Iterable, Optional, Union

import mets_builder
import file_scraper.scraper
from mets_builder.defaults import UNAV
from mets_builder.metadata import (DigitalProvenanceEventMetadata,
                                   DigitalProvenanceAgentMetadata)

import siptools_ng.agent


# Map scraper grades to values of USE attibute
USE = {
    file_scraper.defaults.BIT_LEVEL:
    "fi-dpres-file-format-identification",
    file_scraper.defaults.BIT_LEVEL_WITH_RECOMMENDED:
    "fi-dpres-no-file-format-validation"
}


def _normalize_unav(value):
    """
    Normalize value to "0" if the value is "(:unav)", otherwise return the
    value as-is
    """
    if value == UNAV:
        return "0"

    return value


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


def _create_technical_csv_metadata(
        stream: dict, filepath, has_header
) -> mets_builder.metadata.TechnicalImageMetadata:
    """Create technical csv metadata object from file-scraper stream."""
    first_line = stream["first_line"]
    if has_header:
        header = first_line
    else:
        header = [f"header{n}" for n in range(1, len(first_line) + 1)]

    return mets_builder.metadata.TechnicalCSVMetadata(
        filenames=[filepath],
        header=header,
        charset=stream["charset"],
        delimiter=stream["delimiter"],
        record_separator=stream["separator"],
        quoting_character=stream["quotechar"]
    )


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
        self._csv_has_header = None

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

    def _create_technical_characteristics(self, stream: dict) -> \
            Optional[mets_builder.metadata.TechnicalObjectMetadata]:
        """Generate file/stream format specific metadata.

        Creates for example AudioMD for audio streams, MixMD for image
        and VideoMD for video. Returns ``None`` if technical
        characteristics are not required for the format.

        :param stream: Individual stream metadata as returned by
            file-scraper
        """
        if stream["mimetype"] == "text/csv":
            return _create_technical_csv_metadata(stream,
                                                  self.sip_filepath,
                                                  self._csv_has_header)
        stream_type = stream["stream_type"]
        if stream_type == "image":
            return _create_technical_image_metadata(stream)
        if stream_type == "audio":
            return _create_technical_audio_metadata(stream)
        if stream_type == "video":
            return _create_technical_video_metadata(stream)

        return None

    def generate_technical_metadata(
        self,
        file_format: Optional[str] = None,
        file_format_version: Optional[str] = None,
        checksum_algorithm: Union[
            mets_builder.metadata.ChecksumAlgorithm, str, None
        ] = None,
        checksum: Optional[str] = None,
        file_created_date: Optional[str] = None,
        object_identifier_type: Optional[str] = None,
        object_identifier: Optional[str] = None,
        charset: Union[mets_builder.metadata.Charset, str, None] = None,
        original_name: Optional[str] = None,
        csv_has_header: Optional[bool] = None,
        csv_delimiter: Optional[str] = None,
        csv_record_separator: Optional[str] = None,
        csv_quoting_character: Optional[str] = None,
        format_registry_name: Optional[str] = None,
        format_registry_key: Optional[str] = None,
        creating_application: Optional[str] = None,
        creating_application_version: Optional[str] = None,
    ) -> None:
        """Generate technical metadata for this digital object.

        Scrapes the file found in SIPDigitalObject.source_filepath,
        turning the scraped information into a
        mets_builder.metadata.TechnicalFileObjectMetadata object, and
        finally adds the metadata to this digital object.

        The metadata is overridden or enriched with the user-given
        predefined values, whenever provided. It is possible, however,
        to provide no predefined values at all and use only scraped
        values.

        Also file type specific technical metadata object is created and
        added to the digital object.

        :param file_format: Overrides scraped file format of the object
            with a predefined value. Mimetype of the file, e.g.
            'image/tiff'. When set, predef_file_format_version has to be
            set as well.
        :param file_format_version: Overrides scraped file format
            version of the object with a predefined value. Version
            number of the file format, e.g. '1.2'. When set,
            predef_file_format has to be set as well.
        :param checksum_algorithm: Overrides scraped checksum algorithm
            of the object with a predefined value. The specific
            algorithm used to construct the checksum for the digital
            object. If given as string, the value is cast to
            mets_builder.metadata.ChecksumAlgorithm and results in error
            if it is not a valid checksum algorithm. The allowed values
            can be found from ChecksumAlgorithm documentation. When set,
            predef_checksum has to be set as well.
        :param checksum: Overrides scraped checksum of the object with a
            predefined value. The output of the message digest
            algorithm. When set, predef_checksum_algorithm has to be set
            as well.
        :param file_created_date: Overrides scraped file created date of
            the object with a predefined value. The actual or
            approximate date and time the object was created. The time
            information must be expressed using either the ISO-8601
            format, or its extended version ISO_8601-2.
        :param object_identifier_type: Overrides generated object
            identifier type of the object with a predefined value.
            Standardized identifier types should be used when possible
            (e.g., an ISBN for books). When set,
            predef_object_identifier has to be set as well.
        :param object_identifier: Overrides generated object identifier
            of the object with a predefined value. File identifiers
            should be globally unique. When set,
            predef_object_identifier_type has to be set as well.
        :param charset: Overrides scraped charset of the object with a
            predefined value. Character encoding of the file. If given
            as string, the value is cast to
            mets_builder.metadata.Charset and results in error if it is
            not a valid charset. The allowed values
            can be found from Charset documentation.
        :param original_name: Overrides scraped original name of the
            object with a predefined value.
        :param csv_has_header: A boolean indicating whether this CSV
            file has a header row or not. If set as True, the first row
            of the file is used as header information. If set as False,
            the header metadata is set as "header1", "header2", etc.
            according to the number of fields in a row.
        :param csv_delimiter: Overrides the scraped delimiter
            character(s) with a predefined value. The character or
            combination of characters that are used to separate fields
            in the CSV file.
        :param csv_record_separator: Overrides the scraped record
            separator character(s) with a predefined value. The
            character or combination of characters that are used to
            separate records in the CSV file.
        :param csv_quoting_character: Overrides the scraped quoting
            character with a predefined value. The character that is
            used to encapsulate values in the CSV file. Encapsulated
            values can include characters that are otherwise treated in
            a special way, such as the delimiter character.
        :param format_registry_name: Enriches generated metadata with
            format registry name. Name identifying a format registry, if
            a format registry is used to give further information about
            the file format. When set, format_registry_key has to be set
            as well.
        :param format_registry_key: Enriches generated metadata with
            format registry key. The unique key used to reference an
            entry for this file format in a format registry. When set,
            format_registry_name has to be set as well.
        :param creating_application: Enriches generated metadata with
            creating application. Software that was used to create this
            file. When set, creating_application_version has to be set
            as well.
        :param creating_application_version: Enriches generated metadata
            with creating application version. Version of the software
            that was used to create this file. When set,
            creating_application has to be set as well.
        """
        if self._technical_metadata_generated:
            raise MetadataGenerationError(
                "Technical metadata has already been generated for the "
                "digital object."
            )

        if file_format_version and not file_format:
            raise ValueError(
                "Predefined file format version is given, but file format is "
                "not."
            )
        if checksum_algorithm and not checksum:
            raise ValueError(
                "Predefined checksum algorithm is given, but checksum is not."
            )
        if checksum and not checksum_algorithm:
            raise ValueError(
                "Predefined checksum is given, but checksum algorithm is not."
            )
        if (csv_has_header or csv_delimiter or csv_record_separator
                or csv_quoting_character) and file_format != 'text/csv':
            raise ValueError(
                "CSV specific parameters (csv_has_header, csv_delimiter, "
                "csv_record_separator, csv_quoting_character) can be "
                "used only with CSV files"
            )

        if csv_has_header is not None:
            self._csv_has_header = csv_has_header

        scraper = file_scraper.scraper.Scraper(
            filename=str(self.source_filepath),
            mimetype=file_format,
            version=file_format_version,
            charset=charset,
            delimiter=csv_delimiter,
            separator=csv_record_separator,
            quotechar=csv_quoting_character,
        )
        scraper.scrape(check_wellformed=False)

        stream = scraper.streams[0]

        # Create PREMIS metadata for file
        file_metadata = mets_builder.metadata.TechnicalFileObjectMetadata(
            file_format=scraper.mimetype,
            file_format_version=scraper.version,
            checksum_algorithm=checksum_algorithm or "MD5",
            checksum=checksum or scraper.checksum(algorithm="MD5"),
            file_created_date=file_created_date
            or _file_creation_date(self.source_filepath),
            object_identifier_type=object_identifier_type,
            object_identifier=object_identifier,
            charset=charset or stream.get("charset", None),
            original_name=original_name or self.source_filepath.name,
            format_registry_name=format_registry_name,
            format_registry_key=format_registry_key,
            creating_application=creating_application,
            creating_application_version=creating_application_version
        )
        self.add_metadata(file_metadata)

        # Create file format specific metadata (eg. AudioMD, MixMD,
        # VideoMD)
        characteristics = self._create_technical_characteristics(stream)
        if characteristics:
            self.add_metadata(characteristics)

        # Create metadata for the streams of a given file
        for i, stream in enumerate(scraper.streams.values()):
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

            # Add digital object streams
            digital_object_stream = mets_builder.DigitalObjectStream(
                metadata=[stream_metadata]
            )

            # Generate stream format specific metadata if applicable
            characteristics = self._create_technical_characteristics(stream)
            if characteristics:
                digital_object_stream.add_metadata(characteristics)

            self.add_stream(digital_object_stream)

        # Document file scraping
        if not checksum:
            self._add_checksum_calculation_event()
        if not file_format:
            self._add_format_identification_event(scraper)
        self._add_metadata_extraction_event(scraper)

        # If file-scraper detects the file as "bit-level file" (for
        # example SEG-Y), set the use attribute accordingly.
        self.use = USE.get(scraper.grade())

        self._technical_metadata_generated = True

    def _add_checksum_calculation_event(self):
        """Add checksum calculation event to a digital object."""
        checksum_event = DigitalProvenanceEventMetadata(
            event_type="message digest calculation",
            event_detail="Checksum calculation for digital objects",
            event_outcome="success",
            event_outcome_detail=(
                "Checksum successfully calculated for digital objects."
            )
        )
        file_scraper_agent = siptools_ng.agent.get_file_scraper_agent()

        checksum_event.link_agent_metadata(
            agent_metadata=file_scraper_agent,
            agent_role="executing program"
        )

        self.add_metadata(checksum_event)
        self.add_metadata(file_scraper_agent)

    def _add_metadata_extraction_event(self, scraper):
        """Add metadata extraction event to a digital object."""
        event = DigitalProvenanceEventMetadata(
            event_type="metadata extraction",
            event_detail=("Technical metadata extraction as premis metadata "
                          "from digital objects"),
            event_outcome="success",
            event_outcome_detail=("Premis metadata successfully created "
                                  "from extracted technical metadata."),
        )

        # In addition file-scraper itself, create agent metadata
        # representing each Scraper that was used
        scraper_infos = [
            scraper_info for scraper_info in scraper.info.values()
            if scraper_info['class'].endswith("Scraper")
        ]
        agents = [siptools_ng.agent.get_file_scraper_agent()] \
            + _create_scraper_agents(scraper_infos)
        for agent in agents:
            self.add_metadata(agent)
            event.link_agent_metadata(
                agent_metadata=agent,
                agent_role="executing program"
            )
        self.add_metadata(event)

    def _add_format_identification_event(self, scraper):
        """Add format identification event to a digital object."""
        event = DigitalProvenanceEventMetadata(
            event_type="format identification",
            event_detail="MIME type and version identification",
            event_outcome="success",
            event_outcome_detail=("File MIME type and format version "
                                  "successfully identified."),
        )

        # In addition file-scraper itself, create agent metadata
        # representing each Detector that was used
        detector_infos = [
            scraper_info for scraper_info in scraper.info.values()
            if scraper_info['class'].endswith("Detector")
        ]
        agents = [siptools_ng.agent.get_file_scraper_agent()] \
            + _create_scraper_agents(detector_infos)

        for agent in agents:
            self.add_metadata(agent)
            event.link_agent_metadata(
                agent_metadata=agent,
                agent_role="executing program"
            )

        self.add_metadata(event)

    # TODO: siptools-ng currently does not validate digital objects, so
    # this method is unused.
    def _add_validation_event(self, scraper):
        """Add metadata validation event to a digital object."""
        event = DigitalProvenanceEventMetadata(
            event_type="validation",
            event_detail="Digital object validation",
            event_outcome="success",
            event_outcome_detail=("Digital object(s) evaluated as "
                                  "well-formed and valid."),
        )
        # In addition file-scraper itself, create agent metadata
        # representing each Scraper that was used
        scraper_infos = [
            scraper_info for scraper_info in scraper.info.values()
            if scraper_info['class'].endswith("Scraper")
        ]
        agents = [siptools_ng.agent.get_file_scraper_agent()] \
            + _create_scraper_agents(scraper_infos)
        for agent in agents:
            self.add_metadata(agent)
            event.link_agent_metadata(
                agent_metadata=agent,
                agent_role="executing program"
            )

        self.add_metadata(event)


def _create_scraper_agents(scraper_infos):
    agents = []
    for scraper_info in scraper_infos:
        if scraper_info["tools"]:
            tools = 'Used tools (name-version): ' \
                + ', '.join(scraper_info['tools'])
        else:
            # The scraper/detector does not use any external tools
            # TODO: It probably would not make much sense to create
            # separate agent for this scraper/detector, as agent
            # representing file-scraper will be created anyway. However,
            # tools have not yet been defined for ANY scraper/detector,
            # so it is probably better to create agent for every
            # scraper/detector until the tools have been defined!
            tools = None
        agents.append(
            DigitalProvenanceAgentMetadata(
                agent_name=scraper_info['class'],
                agent_type="software",
                agent_version=file_scraper.__version__,
                agent_note=tools
            )
        )
    return agents
