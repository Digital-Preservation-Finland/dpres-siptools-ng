.. _advanced:

Advanced usage
==============

.. _generating_technical_metadata:

Generating technical metadata
-----------------------------

Siptools-ng usually detects file formats correctly, but it might sometimes
generate wrong technical metadata due to missing context. For example, a CSV
file could be detected as plain text file. The detected file format can be
verified as follows:

.. code-block:: python

   techmd = next(
       metadata for metadata in file.metadata
       if metadata.metadata_type.value == "technical"
       and metadata.metadata_format.value == "PREMIS:OBJECT"
   )
   techmd.file_format  # The detected mimetype of the file, for example "text/plain"

If we know that we are importing a CSV file, we can ensure that it is detected
correctly by generating technical metadata manually using
:meth:`siptools_ng.file.File.generate_technical_metadata` method:

.. code-block:: python

    file.generate_technical_metadata(
        file_format="text/csv", csv_has_header=True
    )

.. note::

   Siptools-ng generates the technical metadata with file-scraper_.
   File-scraper also provides a command-line interface that can be used study
   files without siptools-ng.

Enriching the SIP/files with additional metadata
------------------------------------------------

Both :class:`siptools_ng.sip.SIP` and :class:`siptools_ng.file.File` accept
metadata using the `add_metadata` method. This includes all metadata classes
available in dpres-mets-builder under :mod:`mets_builder.metadata`.

For example, we might know that one of the files was uploaded into collection
management system *ArchiveStar*. We can add an event for this:

.. code-block:: python

    from mets_builder.metadata import DigitalProvenanceEventMetadata, DigitalProvenanceAgentMetadata
    from mets_builder.mets import AgentRole

    file = File(...)

    event = DigitalProvenanceEventMetadata(
        event_type="creation",
        datetime="2024-01-01",
        outcome="success",
        detail=(
            "The file was uploaded into the collection management system ArchiveStar"
        )
    )
    agent = DigitalProvenanceAgentMetadata(
        name="ArchiveStar",
        agent_type="software",
        version="1.2.0"
    )
    event.link_agent_metadata(agent, agent_role="executing program")

    # Add the event into the file. Agent does not need to be added specifically,
    # as it was linked to the event.
    file.add_metadata([event])


Linking files to other files
----------------------------

For example, we might have two versions of the same file: the original non-supported file, and version that has been migrated to a supported file format:

.. code-block:: python

        source_file = File(
            path="example_files/movie.mov",
            digital_object_path="data/movie.mov"
        )
        source_file.generate_technical_metadata()
        outcome_file = File(
            path="example_files/movie.mkv",
            digital_object_path="data/movie.mkv"
        )
        outcome_file.generate_technical_metadata()

The non-supported source file will not pass validation in DPS, so the validation of the non-supported file must be skipped:

.. code-block:: python

        source_file.digital_object.use = "fi-dpres-no-file-format-validation"

To link the files to each other we create a migration event, which is linked to technical metadata of the files:

.. code-block:: python

        event = mets_builder.metadata.DigitalProvenanceEventMetadata(
            event_type = "migration",
            detail = "Normalization of digital object.",
            outcome = "success",
            outcome_detail = ("Source file format has been normalized. Outcome "
                              "object has been created as a result."),
            datetime = "2024-08-14T15:22:00",
        )

        source_file_techmd = next(
            metadata for metadata in source_file.metadata
            if metadata.metadata_type.value == "technical"
            and metadata.metadata_format.value == "PREMIS:OBJECT"
        )
        event.link_object_metadata(
            source_file_techmd,
            object_role="source"
        )
        outcome_file_techmd = next(
            metadata for metadata in outcome_file.metadata
            if metadata.metadata_type.value == "technical"
            and metadata.metadata_format.value == "PREMIS:OBJECT"
        )
        event.link_object_metadata(
            outcome_file_techmd,
            object_role="outcome"
        )

Finally, the event is added to the files:

.. code-block:: python

        source_file.add_metadata([event])
        outcome_file.add_metadata([event])


Modifying and reading the underlying METS object
------------------------------------------------

In the previous sections, siptools-ng has taken care of adding the requested
entries into the underlying METS object.

However, if siptools-ng does not provide the necessary interface for adding
certain entries into the METS (eg. custom structural maps), you can access the
METS and add them manually. The :class:`mets_builder.mets.METS` is available
via `SIP.mets`.

For example, to add a structural map, you can do the following:

.. code-block:: python

    from mets_builder import StructuralMapDiv, StructuralMap

    file1 = File(...)
    file2 = File(...)

    root_div = StructuralMapDiv(
        "custom_div",
        digital_objects=[
            file1.digital_object,
            file2.digital_object
        ],
    )

    # Add the custom div to a structural map
    structural_map = StructuralMap(root_div=root_div)

    # Add the custom structural map to METS and generate file references
    mets.add_structural_maps([structural_map])

.. warning::

   Avoid adding or removing files after you have created the `SIP` instance,
   as this can cause the state between siptools-ng and mets-builder to diverge.

You can also print the in-progress METS document or write it to a file:

.. code-block:: python

    sip = SIP.from_directory(...)

    # Print the METS as a string
    print(sip.mets.to_xml())

    # Write the METS to a file
    sip.mets.write("/home/alice/mets.xml")

For more information on the available METS classes, see `dpres-mets-builder documentation <https://digital-preservation-finland.github.io/dpres-mets-builder/>`_.

.. _dpres-mets-builder: https://github.com/Digital-Preservation-Finland/dpres-mets-builder
.. _file-scraper: https://github.com/Digital-Preservation-Finland/file-scraper
