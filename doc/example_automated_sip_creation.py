"""Example code for automated SIP creation."""
from mets_builder import METS, MetsProfile

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
# according to the directory structure. Descriptive metadata using the EAD3
# schema is added to the METS as well, as at least one descriptive metadata
# element is required per METS.
sip = SIP.from_directory(
    directory_path="example_files",
    mets=mets,
    metadata_xml_paths=["example_metadata/ead3.xml"]
)

sip.finalize(
    output_filepath="result/example-automated-sip.tar",
    sign_key_filepath="../tests/data/rsa-keys.crt"
)
