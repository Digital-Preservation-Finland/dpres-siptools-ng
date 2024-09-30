Usage
=====

Siptools-ng is a wrapper on top of dpres-mets-builder_, providing extended
capabilities to work with the METS document and finalize it into a SIP.

.. note::

   These examples use very simple METS objects as examples. Please see
   dpres-mets-builder_ documentation for more information on METS and
   the different kinds of metadata that can be described using it.

Submission Information Package (SIP)
------------------------------------

The final result ready for submission into the Digital Preservation Service is
the *Submission Information Package* (SIP). The SIP consists of a METS
document, a digital signature and file(s).

The fastest and easiest way to create a SIP is to automatically import a
directory from the local filesystem using the
:meth:`siptools_ng.sip.SIP.from_directory` factory method:

.. code-block:: python

    from mets_builder import METS, MetsProfile
    from siptools_ng.sip import SIP

    mets = METS(
        mets_profile=MetsProfile.RESEARCH_DATA,
        contract_id="urn:uuid:abcd1234-abcd-1234-5678-abcd1234abcd",
        creator_name="Sigmund Sipenthusiast",
        creator_type="INDIVIDUAL"
    )
    sip = SIP.from_directory(mets=mets, path="/path/to/local/directory")

Files can also be imported manually and then added into a SIP using :meth:`siptools_ng.sip.SIP.from_files`:

.. code-block:: python

    from siptools_ng.file import File

    files = [
        File(
            path="/home/sigmund/Videos/source-files/video.mkv",
            digital_object_path="media/video.mkv"
        ),
        File(
            path="/home/sigmund/Documents/pdf-a/document.pdf",
            digital_object_path="documents/document.pdf"
        )
    ]

    sip = SIP.from_files(mets=mets, files=files)

.. warning::

   Do not add or modify File instances after you have created the SIP instance.

Once you have created a SIP using either method, you can export it immediately
using the :meth:`siptools_ng.sip.SIP.finalize` method:

.. code-block:: python

   sip.finalize(
        output_filepath="sip.tar",
        sign_key_filepath="rsa-keys.crt"
    )

.. note::

   `rsa-keys.crt` is the signing key used to create a digital signature for the
   SIP.

   See the `instructions on the National Digital Preservation Service site <https://digitalpreservation.fi/user_guide/deployment>`_
   (in Finnish) for generating this signing key.

The generated `sip.tar` file can then be uploaded into the service.

Files
-----

Handling digital objects is different from ``dpres-mets-builder`` in
``dpres-siptools-ng``. Digital objects are encapsulated using the
:class:`siptools_ng.file.File` class:

.. code-block:: python

    from siptools_ng.file import File

    file = File(
        path="sip_files/artwork.tif",
        sip_filepath="data/artwork.tif"
    )

This enables additional functionality such as generating technical metadata automatically::

    file.generate_technical_metadata()

:meth:`siptools_ng.file.File.generate_technical_metadata` accepts many
parameters to ensure correct technical metadata is entered for the file. For
example, if we know a file we're importing is a CSV file and want to ensure
it's not detected as a plain text file, we can ensure this using:

.. code-block:: python

    file.generate_technical_metadata(csv_has_header=True)

Further reading
---------------

For more comprehensive examples, see :doc:`examples`.

.. _dpres-mets-builder: https://github.com/Digital-Preservation-Finland/dpres-mets-builder
