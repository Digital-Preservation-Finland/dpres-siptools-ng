"""Test digital provenance module."""
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
