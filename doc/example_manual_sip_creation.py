"""Example code for manual SIP creation."""
from mets_builder import (
    METS,
    MetsProfile,
    StructuralMap,
    StructuralMapDiv,
)
from mets_builder.metadata import (
    DigitalProvenanceEventMetadata,
    ImportedMetadata,
)

from siptools_ng.file import File
from siptools_ng.sip import SIP

# A part of using dpres-siptools-ng is to create a METS object using
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

# Create files each containing a digital object which contains the sip path.
file1 = File(
    path="example_files/art/movie.mkv",
    digital_object_path="data/movies/movie.mkv"
)
file2 = File(
    path="example_files/text_files/file1.txt",
    digital_object_path="data/text_files/file1.txt"
)
file3 = File(
    path="example_files/text_files/file2.txt",
    digital_object_path="data/text_files/file2.txt"
)

# Create provenance metadata
provenance_md = DigitalProvenanceEventMetadata(
        event_type="creation",
        detail="This is a detail",
        outcome="success",
        outcome_detail="Another detail",
    )

# Import descriptive metadata from an XML source
descriptive_md = ImportedMetadata.from_path("example_metadata/ead3.xml")

# Add metadata to files
file1.add_metadata([provenance_md])
file2.add_metadata([provenance_md, descriptive_md])
file3.add_metadata([descriptive_md])

# Make a custom structural map div using the digital objects in files
root_div = StructuralMapDiv(
    "custom_div",
    digital_objects=[
        file1.digital_object,
        file2.digital_object,
        file3.digital_object
    ],
)

# Add the custom div to a structural map
structural_map = StructuralMap(root_div=root_div)

# Add the custom structural map to METS and generate file references
mets.add_structural_maps([structural_map])
mets.generate_file_references()

# Make a SIP using the previously created file and METS. In addition to the
# manually structural map a default custom map is generated based on the
# directory structure.
sip = SIP.from_files(mets=mets, files=[file1, file2, file3])

# Finalize the SIP and write it to file
sip.finalize(
    output_filepath="result/example-manual-sip.tar",
    sign_key_filepath="../tests/data/rsa-keys.crt"
)
