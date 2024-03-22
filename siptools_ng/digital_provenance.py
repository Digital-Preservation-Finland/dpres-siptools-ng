"""Module for easy creation of digital provenance metadata."""
from file_scraper import __version__ as file_scraper_version
from mets_builder.metadata import (DigitalProvenanceAgentMetadata,
                                   DigitalProvenanceEventMetadata)

from siptools_ng import __version__
from siptools_ng.sip_digital_object import SIPDigitalObject


def get_siptools_ng_agent() -> DigitalProvenanceAgentMetadata:
    """Return agent metadata representing dpres-siptools-ng itself."""
    return DigitalProvenanceAgentMetadata(
        agent_name="dpres-siptools-ng",
        agent_type="software",
        agent_version=__version__
    )


def get_file_scraper_agent() -> DigitalProvenanceAgentMetadata:
    """Return agent metadata representing file-scraper."""
    return DigitalProvenanceAgentMetadata(
        agent_name="file-scraper",
        agent_type="software",
        agent_version=file_scraper_version
    )


def add_checksum_calculation_event(digital_object: SIPDigitalObject):
    """Add checksum calculation event to a digital object."""
    checksum_event = DigitalProvenanceEventMetadata(
        event_type="message digest calculation",
        event_detail="Checksum calculation for a digital object",
        event_outcome="success",
        event_outcome_detail=(
            "Checksum successfully calculated for the digital object."
        )
    )
    file_scraper_agent = get_file_scraper_agent()

    checksum_event.link_agent_metadata(
        agent_metadata=file_scraper_agent,
        agent_role="executing program"
    )

    digital_object.add_metadata(checksum_event)
    digital_object.add_metadata(file_scraper_agent)
