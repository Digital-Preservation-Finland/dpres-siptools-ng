"""Test digital provenance module."""
from uuid import UUID

from file_scraper import __version__ as file_scraper_version
from mets_builder.metadata import (DigitalProvenanceAgentMetadata,
                                   DigitalProvenanceEventMetadata)

from siptools_ng import __version__, digital_provenance
from siptools_ng.sip_digital_object import SIPDigitalObject


def test_get_siptools_ng_agent():
    """Test that agent representing siptools-ng has correct information."""
    agent = digital_provenance.get_siptools_ng_agent()
    assert agent.agent_name == "dpres-siptools-ng"
    assert agent.agent_type.value == "software"
    assert agent.agent_version == __version__
    assert agent.agent_identifier_type == "UUID"
    assert agent.agent_identifier is None


def test_get_file_scraper_agent():
    """Test that agent representing file-scraper has correct information."""
    agent = digital_provenance.get_file_scraper_agent()
    assert agent.agent_name == "file-scraper"
    assert agent.agent_type.value == "software"
    assert agent.agent_version == file_scraper_version
    assert agent.agent_identifier_type == "UUID"
    assert agent.agent_identifier is None


def test_add_checksum_calculation_event():
    """Test that checksum calculation event can be added to a digital
    object.
    """
    digital_object = SIPDigitalObject(
        source_filepath="tests/data/test_file.txt",
        sip_filepath="sip_data/test_file.txt"
    )
    digital_provenance.add_checksum_calculation_event(digital_object)

    checksum_event = next(
        metadata for metadata in digital_object.metadata
        if (
            isinstance(metadata, DigitalProvenanceEventMetadata)
            and metadata.event_type == "message digest calculation"
        )
    )
    assert checksum_event.event_type == "message digest calculation"
    assert checksum_event.event_detail == (
        "Checksum calculation for a digital object"
    )
    assert checksum_event.event_outcome.value == "success"
    assert checksum_event.event_outcome_detail == (
        "Checksum successfully calculated for the digital object."
    )
    assert checksum_event.event_identifier_type == "UUID"
    assert checksum_event.event_identifier is None

    agent = next(
        metadata for metadata in digital_object.metadata
        if isinstance(metadata, DigitalProvenanceAgentMetadata)
    )
    assert agent == digital_provenance.get_file_scraper_agent()

    linked_agents = [
        linked_agent.agent_metadata
        for linked_agent in checksum_event.linked_agents
    ]
    assert linked_agents == [digital_provenance.get_file_scraper_agent()]
