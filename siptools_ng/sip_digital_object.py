"""Module for handling digital objects in SIP."""
import platform
from datetime import datetime
from pathlib import Path
from typing import Iterable, Optional, Union

import mets_builder
from file_scraper.scraper import Scraper
from mets_builder.defaults import UNAV


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

    def _create_technical_object_metadata(
        self,
        scraper: Scraper,
        stream: dict
    ) -> mets_builder.metadata.TechnicalObjectMetadata:
        """Create technical object metadata object from file-scraper scraper
        and stream.
        """
        return mets_builder.metadata.TechnicalObjectMetadata(
            file_format=scraper.mimetype,
            file_format_version=scraper.version,
            checksum_algorithm="MD5",
            checksum=scraper.checksum(algorithm="MD5"),
            file_created_date=self._file_creation_date(self.source_filepath),
            charset=stream.get("charset", None),
            original_name=self.source_filepath.name
        )

    def _create_technical_image_metadata(
        self,
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
        self,
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
        self,
        stream: dict
    ) -> mets_builder.metadata.TechnicalVideoMetadata:
        """Create technical video metadata from file-scraper stream."""
        return mets_builder.metadata.TechnicalVideoMetadata(
            duration=stream["duration"],
            data_rate=stream["data_rate"],
            bits_per_sample=stream["bits_per_sample"],
            color=stream["color"],
            codec_creator_app=stream["codec_creator_app"],
            codec_creator_app_version=stream["codec_creator_app_version"],
            codec_name=stream["codec_name"],
            codec_quality=stream["codec_quality"],
            data_rate_mode=stream["data_rate_mode"],
            frame_rate=stream["frame_rate"],
            pixels_horizontal=stream["width"],
            pixels_vertical=stream["height"],
            par=stream["par"],
            dar=stream["dar"],
            sampling=stream["sampling"],
            signal_format=stream["signal_format"],
            sound=stream["sound"]
        )

    def generate_technical_metadata(self) -> None:
        """Generate technical object metadata for this digital object.

        Scrapes the file found in SIPDigitalObject.source_filepath, turning the
        scraped information into a
        mets_builder.metadata.TechnicalObjectMetadata object, and finally adds
        the metadata to this digital object.

        For image, audio and video files also corresponding file type specific
        technical metadata object is created and added to the digital object.
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

        metadata = self._create_technical_object_metadata(scraper, stream)
        self.add_metadata(metadata)

        if stream["stream_type"] == "image":
            metadata = self._create_technical_image_metadata(stream)
            self.add_metadata(metadata)
        if stream["stream_type"] == "audio":
            metadata = self._create_technical_audio_metadata(stream)
            self.add_metadata(metadata)
        if stream["stream_type"] == "video":
            metadata = self._create_technical_video_metadata(stream)
            self.add_metadata(metadata)

        self._technical_metadata_generated = True
