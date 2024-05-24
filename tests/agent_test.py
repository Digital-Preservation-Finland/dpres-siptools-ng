"""Test digital provenance module."""
import file_scraper

import siptools_ng.agent


def test_get_siptools_ng_agent():
    """Test that agent representing siptools-ng has correct information."""
    agent = siptools_ng.agent.get_siptools_ng_agent()
    assert agent.agent_name == "dpres-siptools-ng"
    assert agent.agent_type.value == "software"
    assert agent.agent_version == siptools_ng.__version__
    assert agent.agent_identifier_type == "UUID"
    assert agent.agent_identifier is None


def test_get_file_scraper_agent():
    """Test that agent representing file-scraper has correct information."""
    agent = siptools_ng.agent.get_file_scraper_agent()
    assert agent.agent_name == "file-scraper"
    assert agent.agent_type.value == "software"
    assert agent.agent_version == file_scraper.__version__
    assert agent.agent_identifier_type == "UUID"
    assert agent.agent_identifier is None
