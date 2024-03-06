"""Module for easy creation of digital provenance metadata."""
from file_scraper import __version__ as file_scraper_version
from mets_builder.metadata import DigitalProvenanceAgentMetadata

from siptools_ng import __version__


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
