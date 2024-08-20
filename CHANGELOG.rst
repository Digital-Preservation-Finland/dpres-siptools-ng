Changelog
=========
All notable changes to this project will be documented in this file.

The format is based on `Keep a Changelog <https://keepachangelog.com/en/1.0.0/>`_,
and this project adheres to `Semantic Versioning <https://semver.org/spec/v2.0.0.html>`_.

Unreleased
----------
Added
^^^^^
- Automatic creation of PREMIS events when adding imported metadata to structural map
- Ability to create structural maps from directory structures
- Create a structural map automatically from directory structure when creating SIPs using ``SIP.from_directory``` or ``SIP.from_files``
- ```siptools_ng.sip.structural_map_from_directory_structure``` will now avoid creating unnecessary metadata references by linking shared metadata entries to the directory div instead of to each file individually
- Allow automatically importing external XML metadata to SIP using ``metadata_xml_paths`` and ``metadata_xml_strings`` kwargs in ``SIP.from_directory`` and ``SIP.from_files``

Changed
^^^^^^^
- Rename ``SIPDigitalObject`` to ``File``
- Rename ``File`` class attribute ``source_filepath`` to ``path``
- Rename ``File`` class attribute ``sip_filepath`` to ``digital_object_path``
- Use LABEL attribute for directory names instead of TYPE in structural map divs

0.1.0 - 2024-03-27
------------------
Added
^^^^^
- Method ``SIPDigitalObject.generate_technical_csv_metadata()`` to generate CSV metadata
- Generate stream metadata in ``SIPDigitalObject.generate_technical_metadata()``
- Method ``SIP.from_directory`` to generate a SIP object according to the contents of a directory
- Generate checksum calculation events in ``SIPDigitalObject.generate_technical_metadata()``

Changed
^^^^^^^
- Video metadata (VideoMD) is generated in ``SIPDigitalObject.generate_technical_metadata()``
- Audio metadata (AudioMD) is generated in ``SIPDigitalObject.generate_technical_metadata()``

Fixed
^^^^^
- Fix invalid technical metadata values by normalizing ``(:unav)`` to ``0`` when applicable

0.0.2 - 2023-06-14
------------------
Added
^^^^^
- ``requirements_github.txt`` for end user dependency installation

0.0.1 - 2023-04-19
------------------
- First public release
