"""Module for Submission Information Package (SIP) handling."""
import shutil
from datetime import datetime
from pathlib import Path
from typing import Union

import dpres_signature.signature
import mets_builder

METS_FILENAME = "mets.xml"
SIGNATURE_FILENAME = "signature.sig"


class SIP:
    """Class for Submission Information Package (SIP) handling."""

    def __init__(self, mets: mets_builder.METS) -> None:
        """Constructor for SIP class.

        :param mets: METS object representing the METS file of this SIP.
        """
        self.mets = mets

    def finalize(
        self,
        output_filepath: Union[str, Path],
        sign_key_filepath: Union[str, Path],
        tmp_filepath: Union[str, Path, None] = None
    ) -> None:
        """Build the SIP.

        :param output_filepath: Path where the SIP is built to.
        :param sign_key_filepath: Path to the signature key file that is used
            to sign the SIP.
        :param tmp_filepath: Path where temporary files are stored. If None,
            path is set to '/tmp/siptools-ng/YYYY-MM-DDTHH:MM:SS'.
        """
        if len(self.mets.digital_objects) == 0:
            raise ValueError("SIP does not contain any digital objects.")

        output_filepath = Path(output_filepath)
        output_filepath.mkdir()

        if tmp_filepath is None:
            current_time = datetime.now().isoformat(timespec="seconds")
            tmp_filepath = Path("/tmp/siptools-ng") / current_time
        tmp_filepath = Path(tmp_filepath)
        tmp_filepath.mkdir(parents=True)

        mets_tmp_filepath = self._write_mets(tmp_filepath)

        signature_tmp_filepath = self._write_signature(
            tmp_filepath, str(sign_key_filepath)
        )

        # Copy temporary files to final location
        shutil.copy(
            str(mets_tmp_filepath),
            str(output_filepath / METS_FILENAME)
        )
        shutil.copy(
            str(signature_tmp_filepath),
            str(output_filepath / SIGNATURE_FILENAME)
        )

        self._copy_digital_objects_to_sip(output_filepath)

    def _write_mets(self, output_directory: Path) -> Path:
        """Write the METS document to given directory.

        :param output_directory: Path to the directory where to write the METS
            file.

        :returns: Path where the METS file was written to.
        """
        mets_filepath = output_directory / METS_FILENAME
        self.mets.write(mets_filepath)
        return mets_filepath

    def _copy_digital_objects_to_sip(self, output_filepath: Path) -> None:
        """Copy the digital objects to their target location in the SIP.

        :param output_filepath: Filepath where the SIP is created to.
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
