"""Module for Submission Information Package (SIP) handling."""
import shutil
from pathlib import Path
from typing import Union

import mets_builder

METS_FILENAME = "mets.xml"


class SIP:
    """Class for Submission Information Package (SIP) handling."""

    def __init__(self, mets: mets_builder.METS) -> None:
        """Constructor for SIP class.

        :param mets: METS object representing the METS file of this SIP.
        :type mets: METS
        """
        self.mets = mets

    def finalize(self, output_filepath: Union[str, Path]) -> None:
        """Build the SIP.

        :param output_filepath: Path where the SIP is built to.
        :type output_filepath: Union[str, Path]
        """
        if len(self.mets.digital_objects) == 0:
            raise ValueError("SIP does not contain any digital objects.")

        output_filepath = Path(output_filepath)
        output_filepath.mkdir()

        self._write_mets_to_sip(output_filepath)
        self._copy_digital_objects_to_sip(output_filepath)

    def _write_mets_to_sip(self, output_filepath: Path) -> None:
        """Write the METS object to its target location in the SIP.

        :param output_filepath: Path to the directory where to write the METS
            file.
        :type output_filepath: Path
        """
        mets_filepath = output_filepath / METS_FILENAME
        self.mets.write(mets_filepath)

    def _copy_digital_objects_to_sip(self, output_filepath: Path) -> None:
        """Copy the digital objects to their target location in the SIP.

        :param output_filepath: Filepath where the SIP is created to.
        :type output_filepath: Path
        """
        for digital_object in self.mets.digital_objects:
            digital_object_parent_dir = (
                output_filepath / Path(digital_object.sip_filepath).parent
            )
            digital_object_parent_dir.mkdir(parents=True, exist_ok=True)

            shutil.copy(
               str(digital_object.source_filepath),
               str(output_filepath / digital_object.sip_filepath)
            )
