Changelog
=========
All notable changes to this project will be documented in this file.

The format is based on `Keep a Changelog <https://keepachangelog.com/en/1.0.0/>`_,
and this project adheres to `Semantic Versioning <https://semver.org/spec/v2.0.0.html>`_.

1.1.1 - 2025-05-27
------------------

Fixed
^^^^^
- Unnecessary PREMIS agent metadata is not created for detectors/scrapers of
  file-scraper, that do not use any external tools
- The missing version of used tools was added to notes in PREMIS agent metadata of detectors/scrapers

1.1.0 - 2025-04-10
------------------
Changed
^^^^^^^
- Normalize checksums to lowercase in file technical metadata

Fixed
^^^^^
- Skip technical metadata element generation for bit-level files. This could cause crashes due to metadata being incompatible or incomplete.

1.0.0 - 2024-09-09
------------------
Added
^^^^^
- Automatic creation of PREMIS events when adding imported metadata to SIP
- Automatic creation of default structural map for each SIP object

Changed
^^^^^^^
- Replaced ``SIPDigitalObject`` with ``File``
- Metadata can be added to SIP or specific files using ``SIP.add_metadata`` and ``File.add_metadata``

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
