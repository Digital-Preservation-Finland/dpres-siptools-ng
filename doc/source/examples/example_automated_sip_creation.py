"""Example code for automated SIP creation."""
from mets_builder import METS, MetsProfile
from mets_builder.metadata import (
    DigitalProvenanceEventMetadata,
    ImportedMetadata,
)

from siptools_ng.sip import SIP

# Initialize dpres-mets-builder METS object with your information
mets = METS(
    mets_profile=MetsProfile.RESEARCH_DATA,
    contract_id="urn:uuid:abcd1234-abcd-1234-5678-abcd1234abcd",
    creator_name="Sigmund Sipenthusiast",
    creator_type="INDIVIDUAL"
)

# A prepared directory with all the files to package can be turned into a SIP
# with from_directory method. Here the technical metadata is generated for all
# the files found in the given directory and the structural map is organized
# according to the directory structure.
sip = SIP.from_directory(
    directory_path="example_files",
    mets=mets,
)

# Create provenance metadata and add it to SIP
provenance_md = DigitalProvenanceEventMetadata(
    event_type="creation",
    detail="This is a detail",
    outcome="success",
    outcome_detail="Another detail",
)
sip.add_metadata([provenance_md])

# Import descriptive metadata from an XML source, and add it to SIP
descriptive_md = ImportedMetadata.from_path("example_metadata/ead3.xml")
sip.add_metadata([descriptive_md])

sip.finalize(
    output_filepath="result/example-automated-sip.tar",
    sign_key_filepath="data/rsa-keys.crt"
)
