"""Module for creating agent metadata."""
from file_scraper import __version__ as file_scraper_version
from mets_builder.metadata import DigitalProvenanceAgentMetadata

from siptools_ng import __version__


def get_siptools_ng_agent() -> DigitalProvenanceAgentMetadata:
    """Return agent metadata representing dpres-siptools-ng itself."""
    return DigitalProvenanceAgentMetadata(
        name="dpres-siptools-ng",
        agent_type="software",
        version=__version__
    )


def get_file_scraper_agent() -> DigitalProvenanceAgentMetadata:
    """Return agent metadata representing file-scraper."""
    return DigitalProvenanceAgentMetadata(
        name="file-scraper",
        agent_type="software",
        version=file_scraper_version
    )
