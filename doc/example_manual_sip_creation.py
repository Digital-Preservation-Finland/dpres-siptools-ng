"""Example code for manual SIP creation."""
from mets_builder import METS, MetsProfile, StructuralMap

from siptools_ng.sip import SIP
from siptools_ng.sip_digital_object import SIPDigitalObject

# A big part of using dpres-siptools-ng is to create a METS object using
# dpres-mets-builder in tandem with some helper utilities provided by
# dpres-siptools-ng whenever needed. See user documentation of
# dpres-mets-builder at
# https://github.com/Digital-Preservation-Finland/dpres-mets-builder for more
# detailed instructions on how to build METS objects. This example code focuses
# on automating the METS creation as much as possible.

# Initialize dpres-mets-builder METS object with your information
mets = METS(
    mets_profile=MetsProfile.CULTURAL_HERITAGE,
    contract_id="urn:uuid:abcd1234-abcd-1234-5678-abcd1234abcd",
    creator_name="CSC – IT Center for Science Ltd.",
    creator_type="ORGANIZATION"
)

# Create digital objects and add metadata to them.
#
# A SIPDigitalObject instance should be created for each file to be included in
# the SIP. SIPDigitalObject can be used in a similarly to the
# dpres-mets-builder-class DigitalObject and dpres-mets-builder documentation
# regarding DigitalObjects apply to SIPDigitalObjects as well.
digital_object = SIPDigitalObject(
    source_filepath="example_files/art/movie.mkv",
    sip_filepath="data/files/movie.mkv"
)

# The technical metadata for the digital object can be generated automatically
# with generate_technical_metadata method. For manual metadata creation see
# dpres-mets-builder usage documentation.
digital_object.generate_technical_metadata()

# Create structural map. Here done using the helper method
# from_directory_strucure to generate a structural map according to the
# directory structure. For manual structural map creation see
# dpres-mets-builder usage documentation.
structural_map = StructuralMap.from_directory_structure([digital_object])
mets.add_structural_map(structural_map)

# Generate file references. For manual file references creation see
# dpres-mets-builder usage documentation.
mets.generate_file_references()

# Turn the METS object into a SIP
sip = SIP(mets=mets)
sip.finalize(
    output_filepath="result/example-manual-sip.tar",
    sign_key_filepath="../tests/data/rsa-keys.crt"
)
