"""Module for easy creation of digital provenance metadata."""
from datetime import datetime, timezone

from file_scraper import __version__ as file_scraper_version
from mets_builder.metadata import (DigitalProvenanceAgentMetadata,
                                   DigitalProvenanceEventMetadata)

from siptools_ng import __version__
from siptools_ng.sip_digital_object import SIPDigitalObject

# Use common timestamp for digital provenance metadata created in this module.
# This way we can have a single entry for events in the final METS, rather than
# having multiple entries of the same event with identical information apart
# from the timestamp
_start_time = datetime.now(timezone.utc).isoformat(timespec="seconds")


def get_siptools_ng_agent() -> DigitalProvenanceAgentMetadata:
    """Return agent metadata representing dpres-siptools-ng itself."""
    return DigitalProvenanceAgentMetadata(
        agent_name="dpres-siptools-ng",
        agent_type="software",
        agent_version=__version__,
        agent_identifier_type="local",
        agent_identifier=f"fi-dpres-dpres-siptools-ng-{__version__}"
    )


def get_file_scraper_agent() -> DigitalProvenanceAgentMetadata:
    """Return agent metadata representing file-scraper."""
    return DigitalProvenanceAgentMetadata(
        agent_name="file-scraper",
        agent_type="software",
        agent_version=file_scraper_version,
        agent_identifier_type="local",
        agent_identifier=f"fi-dpres-file-scraper-{file_scraper_version}"
    )


def add_checksum_calculation_event(digital_object: SIPDigitalObject):
    """Add checksum calculation event to a digital object."""
    checksum_event = DigitalProvenanceEventMetadata(
        event_type="message digest calculation",
        event_datetime=_start_time,
        event_detail="Checksum calculation for a digital object",
        event_outcome="success",
        event_outcome_detail=(
            "Checksum successfully calculated for the digital object."
        ),
        event_identifier_type="local",
        event_identifier="fi-dpres-checksum-calculation"
    )
    file_scraper_agent = get_file_scraper_agent()

    checksum_event.link_agent_metadata(
        agent_metadata=file_scraper_agent,
        agent_role="executing program"
    )

    digital_object.add_metadata(checksum_event)
    digital_object.add_metadata(file_scraper_agent)
