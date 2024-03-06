"""Test digital provenance module."""
from file_scraper import __version__ as file_scraper_version

from siptools_ng import __version__, digital_provenance


def test_get_siptools_ng_agent():
    """Test that agent representing siptools-ng has correct information."""
    agent = digital_provenance.get_siptools_ng_agent()
    assert agent.agent_name == "dpres-siptools-ng"
    assert agent.agent_type.value == "software"
    assert agent.agent_version == __version__
    assert agent.agent_identifier_type == "local"
    assert agent.agent_identifier == (
        f"fi-dpres-dpres-siptools-ng-{__version__}"
    )


def test_get_file_scraper_agent():
    """Test that agent representing file-scraper has correct information."""
    agent = digital_provenance.get_file_scraper_agent()
    assert agent.agent_name == "file-scraper"
    assert agent.agent_type.value == "software"
    assert agent.agent_version == file_scraper_version
    assert agent.agent_identifier_type == "local"
    assert agent.agent_identifier == (
        f"fi-dpres-file-scraper-{file_scraper_version}"
    )
