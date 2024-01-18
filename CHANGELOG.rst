Changelog
=========
All notable changes to this project will be documented in this file.

The format is based on `Keep a Changelog <https://keepachangelog.com/en/1.0.0/>`_,
and this project adheres to `Semantic Versioning <https://semver.org/spec/v2.0.0.html>`_.

Unreleased
----------
Added
^^^^^
- Method ``SIPDigitalObject.generate_technical_csv_metadata()`` to generate CSV metadata
- Generate stream metadata in ``SIPDigitalObject.generate_technical_metadata()``

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
