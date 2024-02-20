"""Module for easy creation of digital provenance metadata."""
from mets_builder.metadata import DigitalProvenanceAgentMetadata

from siptools_ng import __version__


def dpres_siptools_ng() -> DigitalProvenanceAgentMetadata:
    """Return agent metadata representing dpres-siptools-ng itself."""
    return DigitalProvenanceAgentMetadata(
        agent_name="dpres-siptools-ng",
        agent_type="software",
        agent_version=__version__,
        agent_identifier_type="local",
        agent_identifier=f"fi-dpres-dpres-siptools-ng-{__version__}"
    )
