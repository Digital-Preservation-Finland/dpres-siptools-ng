"""Module for Submission Information Package (SIP) handling."""
import tarfile
import tempfile
from collections import defaultdict
from collections.abc import Iterable
from pathlib import Path, PurePath
from typing import Optional, Union

import dpres_signature.signature
import mets_builder
from mets_builder.digital_object import DigitalObject
from mets_builder.metadata import (DigitalProvenanceAgentMetadata,
                                   DigitalProvenanceEventMetadata,
                                   ImportedMetadata, Metadata)
from mets_builder.structural_map import StructuralMap, StructuralMapDiv

import siptools_ng.agent
from siptools_ng.file import File

METS_FILENAME = "mets.xml"
SIGNATURE_FILENAME = "signature.sig"


class SIP:
    """Class for Submission Information Package (SIP) handling."""

    def __init__(
            self,
            mets: mets_builder.METS,
            files: Optional[Iterable[File]] = None
    ) -> None:
        """Constructor for SIP class.

        .. note:: To create a SIP from existing directory or files you
                  should instead use :meth:``SIP.from_directory``
                  or :meth:``SIP.from_files``.

        :param mets: METS object representing the METS file of this SIP.
        :param files: Files to be added into the SIP.
        """
        self.mets = mets

        self.files = []
        if files:
            self.files = files

    def finalize(
        self,
        output_filepath: Union[str, Path],
        sign_key_filepath: Union[str, Path]
    ) -> None:
        """Build the SIP.

        The SIP will be built to the given output filepath, packed as a tar
        file. The SIP will contain the METS object of this SIP object
        serialized as an XML file, a signature file that signs the serialized
        METS document, and the digital objects declared in the METS object of
        this SIP object.

        The SIP will appear with '.tmp' suffix until finished.

        :param output_filepath: Path where the SIP is built to.
        :param sign_key_filepath: Path to the signature key file that is used
            to sign the SIP.
        """
        if not self.mets.digital_objects:
            raise ValueError("SIP does not contain any digital objects.")

        output_filepath = Path(output_filepath)
        if output_filepath.exists():
            raise FileExistsError(
                f"Given output filepath '{output_filepath}' exists already."
            )

        with tempfile.TemporaryDirectory(prefix="siptools-ng_") as tmp_dir:
            tmp_path = Path(tmp_dir)

            mets_tmp_filepath = self._write_mets(tmp_path)
            signature_tmp_filepath = self._write_signature(
                tmp_path, str(sign_key_filepath)
            )
            self._write_sip(
                output_filepath, mets_tmp_filepath, signature_tmp_filepath
            )

    def _write_mets(self, output_directory: Path) -> Path:
        """Write the METS document to given directory.

        :param output_directory: Path to the directory where to write the METS
            file.

        :returns: Path where the METS file was written to.
        """
        mets_filepath = output_directory / METS_FILENAME
        self.mets.write(mets_filepath)
        return mets_filepath

    def _write_signature(
        self,
        output_directory: Path,
        sign_key_filepath: str
    ) -> Path:
        """Write a signature file signing the METS document.

        Assumes that given output_directory contains a METS document named
        'mets.xml'.

        :param output_directory: Path where to write the signature file. Should
            also contain a file named 'mets.xml', that is the METS document to
            sign with this signature file.
        :param sign_key_filepath: Path to the signature key file.

        :returns: Path where the signature file was written to.
        """
        signature = dpres_signature.signature.create_signature(
            output_directory, sign_key_filepath, [METS_FILENAME]
        )

        signature_filepath = output_directory / SIGNATURE_FILENAME
        signature_filepath.write_bytes(signature)
        return signature_filepath

    def _write_sip(
        self,
        output_filepath: Path,
        mets_filepath: Path,
        signature_filepath: Path
    ) -> None:
        """Write contents of the SIP to a tar file.

        Writes the METS document, signature file and digital objects of the
        SIP, packing them into a tar file. The SIP will be written to the given
        output path, appearing with '.tmp' suffix until finished.

        :param output_filepath: Path where the SIP is written to.
        :param mets_filepath: Filepath to the METS document (written in
            advance) that is included in this SIP.
        :param signature_filepath: Filepath to the signature file (written in
            advance) that is included in this SIP.
        """
        tmp_digital_object_path = Path(f"{output_filepath}.tmp")
        with tarfile.open(tmp_digital_object_path, "w") as tarred_sip:
            tarred_sip.add(name=mets_filepath, arcname=METS_FILENAME)
            tarred_sip.add(name=signature_filepath, arcname=SIGNATURE_FILENAME)
            for file in self.files:
                tarred_sip.add(
                    name=file.path,
                    arcname=file.digital_object.path
                )

        tmp_digital_object_path.rename(output_filepath)

    def _create_default_structural_map(self) -> None:
        """Automatically generates a default structural map based on the
        directory structure.
        """
        digital_objects = []
        for file in self.files:
            digital_objects.append(file.digital_object)
        if digital_objects:
            structural_map = _structural_map_from_directory_structure(
                digital_objects=digital_objects,
                additional_agents=[siptools_ng.agent.get_siptools_ng_agent()]
            )
            self.mets.add_structural_map(structural_map)
            self.mets.generate_file_references()

    @classmethod
    def from_files(
        cls,
        mets: mets_builder.METS,
        files: Iterable[File]
    ) -> "SIP":
        """Generate a complete SIP object from a list of File instances.

        Technical metadata is generated for given files if missing, and
        structural map is generated according to the directory structure
        defined in the files.

        :param mets: Initialized METS object. The METS object will be populated
                     with additional entries (structural map, agents, events).
        :param files: File instances. Technical metadata is automatically
                      generated for those that don't already have it.

        :returns: SIP object initialized according to the given files
        """
        for file in files:
            if not file._technical_metadata_generated:
                file.generate_technical_metadata()

        sip = cls(mets=mets, files=files)
        sip._create_default_structural_map()
        return sip

    @classmethod
    def from_directory(
        cls,
        directory_path: Union[Path, str],
        mets: mets_builder.METS
    ) -> "SIP":
        """Generate a SIP object according to the contents of a directory.

        All files found in the directory tree are detected and technical
        metadata generated for the files. Structural map is generated according
        to the directory structure found in the given directory_path, and
        simple file references are generated.

        :param directory_path: Path to a local directory.
        :param mets: Initialized METS object. This METS object will be edited
            in place by this method to represent the files and the directory
            structure in the given directory_path.

        :raises: ValueError if the given directory_path does not exist or is
            not a directory.

        :returns: SIP object initialized according to the directory structure
            in the given path.
        """
        directory_path = Path(directory_path)
        if not directory_path.exists():
            raise ValueError(f"Path '{str(directory_path)}' does not exist.")
        if not directory_path.is_dir():
            raise ValueError(
                f"Path '{str(directory_path)}' is not a directory."
            )

        file_paths = {
            path for path in directory_path.rglob("*") if path.is_file()}

        files = {
            File(
                path=file_,
                digital_object_path=file_.relative_to(directory_path.parent)
            )
            for file_ in file_paths
        }

        # Pass the generated File instances to `SIP.from_files`, which
        # will handle rest of the automatic SIP creation.
        return cls.from_files(mets=mets, files=files)


def _structural_map_from_directory_structure(
    digital_objects: Iterable[DigitalObject],
    additional_agents:
        Optional[Iterable[DigitalProvenanceAgentMetadata]] = None
) -> StructuralMap:
    """Generate a structural map according to the directory structure of the
    digital objects.

    Returns a StructuralMap instance with StructuralMapDivs generated and
    DigitalObjects added to the generated StructuralMapDivs according to
    the directory structure as inferred from the digital_object_path attributes
    of the given digital objects.

    The div labels will be set to be the same as the corresponding directory
    name and div type is "directory". The entire div tree will be placed into a
    wrapping div with type "directory".

    For example, if three digital objects are given, and their respective
    digital_object_path attributes are:
    - "data/directory_1/file_1.txt"
    - "data/directory_1/file_2.txt"
    - "data/directory_2/file_3.txt"

    Then this method will create a structural map with:
    - root div with type "directory"
    - div with type "data" inside the root div
    - div with type "directory_1", added to the "data" div
    - div with type "directory_2", added to the "data" div
    - the DigitalObjects representing "file_1.txt" and "file_2.txt" added
      to the "directory_1" div
    - the DigitalObject representing "file_3.txt" added to the
      "directory_2" div

    The structural map generation process is also documented as digital
    provenance metadata (event and the executing agent) that are added to
    the root div of the generated structural map. The event type is
    'creation' and the agent linked to the event as the executing program
    is dpres-mets-builder.

    :param digital_objects: The DigitalObject instances that are used to
        generate the structural map
    :param additional_agents: Digital provenance agent metadata to be added
        as additional executing programs for the structural map creation
        event. These agents will be added alongside dpres-mets-builder as
        executing programs for the event, and as metadata for the root
        div of the structural map. This parameter can be used to document
        the involvement of other programs that call this method to create
        the structural map.

    :raises: ValueError if 'digital_objects' is empty.

    :returns: A StructuralMap instance structured according to the
        directory structure inferred from the given digital objects
    """
    if not digital_objects:
        raise ValueError(
            "Given 'digital_objects' is empty. Structural map can not be "
            "generated with zero digital objects."
        )

    structural_map = StructuralMap(StructuralMapDiv(div_type="directory"),
                                   structural_map_type='PHYSICAL')

    # dict directory filepath -> corresponding div
    # In the algorithm below, PurePath(".") can be thought of as the root
    # div that has already been created, initialize the dict with that
    path2div = {PurePath("."): structural_map.root_div}

    # dict directory filepath -> child directory filepaths
    directory_relationships = defaultdict(set)

    for digital_object in digital_objects:

        digital_object_path = PurePath(digital_object.path)

        for path in digital_object_path.parents:
            # Do not process path "."
            if path == PurePath("."):
                continue

            # Create corresponding div for directories if they do not exist yet
            if path not in path2div:
                path2div[path] = StructuralMapDiv(
                    div_type="directory",
                    label=path.name
                )

            # Save directory relationships to be dealt with later
            directory_relationships[path.parent].add(path)

        # Create a wrapper div for the digital object and add it to parent div
        wrapper_div = StructuralMapDiv(
            div_type="file",
            label=Path(digital_object.path).name
        )
        wrapper_div.add_digital_objects([digital_object])
        path2div[digital_object_path.parent].divs.add(wrapper_div)

    # Nest divs according to the directory structure
    for parent_dir, child_dirs in directory_relationships.items():
        parent_div = path2div[parent_dir]
        child_divs = {path2div[directory] for directory in child_dirs}
        parent_div.add_divs(child_divs)

    # Document the process as digital provenance metadata
    _add_digital_provenance_for_structural_map_creation(
        structural_map, additional_agents
    )

    # Bundle metadata recursively
    structural_map.root_div.bundle_metadata()

    return structural_map


def _add_digital_provenance_for_structural_map_creation(
    structural_map,
    additional_agents=None
):
    """Creates digital provenance metadata for structural map creation.

    Creates an event for structural map creation, an agent representing
    dpres-mets-builder, and links the agent as an agent for the event. Also
    adds the event and agent as metadata for the root div.

    :param root_div: The root div of the structural map in question
    :param additional_agents: Optional agents to be linked to the event
        additionally to the dpres-mets-builder agent, and added as metadata to
        the root_div
    """
    if additional_agents is None:
        additional_agents = []

    event = DigitalProvenanceEventMetadata(
        event_type="creation",
        detail=(
            "Creation of structural metadata with the "
            "StructuralMap.from_directory_structure method"
        ),
        outcome="success",
        outcome_detail=(
            f"Created METS structural map with type "
            f"'{structural_map.structural_map_type}'"
        )
    )
    mets_builder_agent = \
        DigitalProvenanceAgentMetadata.get_mets_builder_agent()

    for agent in [mets_builder_agent] + additional_agents:
        event.link_agent_metadata(
            agent_metadata=agent,
            agent_role="executing program"
        )

    for metadata in [event, mets_builder_agent] + additional_agents:
        _add_metadata(structural_map.root_div, metadata)


def _add_metadata(div: StructuralMapDiv,
                  metadata: Metadata):
    """Add metadata to a given div.

    The metadata should apply to all digital objects under this div (as
    well as digital objects under the divs nested in this div)

    If metadata is imported metadata, also an event that describes
    the import process is added to div.

    :param div: The div that the metadata object is added to.

    :param metadata: The metadata object that is added.
    """
    if isinstance(metadata, ImportedMetadata):
        event = DigitalProvenanceEventMetadata(
            event_type="metadata extraction",
            detail="Descriptive metadata import from external source",
            outcome="success",
            outcome_detail=(
                "Descriptive metadata imported to "
                "mets dmdSec from external source"
            )
        )
        div.add_metadata(event)
    div.add_metadata(metadata)
