"""Module for Submission Information Package (SIP) handling."""
import tarfile
import tempfile
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
        sign_key_filepath: Union[str, Path]
    ) -> None:
        """Build the SIP.

        The SIP will be built to the given output filepath, packed as a tar
        file. The SIP will contain the METS object of this SIP object
        serialized as an XML file, a signature file that signs the serialized
        METS document, and the digital objects declared in the METS object of
        this SIP object.

        :param output_filepath: Path where the SIP is built to.
        :param sign_key_filepath: Path to the signature key file that is used
            to sign the SIP.
        """
        if len(self.mets.digital_objects) == 0:
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
            self._pack_files_to_tar(
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

    def _pack_files_to_tar(
        self,
        output_filepath: Path,
        mets_filepath: Path,
        signature_filepath: Path
    ) -> None:
        """Pack contents of the SIP to a tar file.

        Packs the METS document, signature file and digital objects of the SIP.

        :param output_filepath: Filepath where the packed SIP is written to.
        :param mets_filepath: Filepath to the METS document (written in
            advance) that is included in this SIP.
        :param signature_filepath: Filepath to the signature file (written in
            advance) that is included in this SIP.
        """
        with tarfile.open(output_filepath, "w") as tarred_sip:
            tarred_sip.add(name=mets_filepath, arcname=METS_FILENAME)
            tarred_sip.add(name=signature_filepath, arcname=SIGNATURE_FILENAME)
            for digital_object in self.mets.digital_objects:
                tarred_sip.add(
                    name=digital_object.source_filepath,
                    arcname=digital_object.sip_filepath
                )
