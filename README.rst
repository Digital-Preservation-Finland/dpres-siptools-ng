**NOTE: The project is not ready for production use. It is published prematurely to give an opportunity
to get acquainted with the project in advance and to get feedback.**

To give feedback, please open a GitHub issue or pull request.

dpres-siptools-ng
=================

Library for creating Submission Information Packages (SIP) that comply to the specifications of
national digital preservation services of Finland.

Requirements
------------

Installation and usage requires Python 3.9 or newer.
To use siptools-ng you will also have to install file-scraper and it's dependencies.
See https://github.com/Digital-Preservation-Finland/file-scraper for instructions.

The software is tested with Python 3.9 on AlmaLinux 9 release.

Installation using RPM packages (preferred)
-------------------------------------------

Installation on Linux distributions is done by using the RPM Package Manager.
See how to `configure the PAS-jakelu RPM repositories`_ to setup necessary software sources.

.. _configure the PAS-jakelu RPM repositories: https://www.digitalpreservation.fi/user_guide/installation_of_tools 

After the repository has been added, the package can be installed by running the following command::

    sudo dnf install python3-dpres-siptools-ng

Usage
-----

Siptools-ng is a layer on top of `dpres-mets-builder <https://github.com/Digital-Preservation-Finland/dpres-mets-builder>`_, providing extended capabilities to work with the METS document and finalize it into a SIP. 

Handling digital objects is different from ``dpres-mets-builder`` in ``dpres-siptools-ng``. Digital objects should be handled using the ``SIPDigitalObject`` class::

    from siptools_ng.sip_digital_object import SIPDigitalObject

    digital_object = SIPDigitalObject(
        source_filepath="sip_files/artwork.tif",
        sip_filepath="data/artwork.tif"
    )

In addition to adding metadata to digital objects like in ``dpres-mets-builder``, ``dpres-siptools-ng`` provides a function to generate the technical metadata automatically::

    digital_object.generate_technical_metadata()

However, CSV files require some aditional information, so there is a separate method to generate technical metadata for CSV files::

    digital_object.generate_technical_csv_metadata(has_header=True)

See the usage documentation of ``dpres-mets-builder`` for instructions to build a ``METS`` object (replacing digital object handling with ``SIPDigitalObject``), and turn it into a SIP with the following commands::

    from mets_builder import METS
    from siptools_ng.sip import SIP

    mets = METS(...)

    # ...build the METS...

    sip = SIP(mets=mets)
    sip.finalize(
        output_filepath="sip.tar",
        sign_key_filepath="rsa-keys.crt"
    )

Also, if a directory with all the files to package has been prepared, a SIP where the technical metadata is generated for all the files found in the directory and the structural map is organized according to the directory structure can be kickstarted with a single method::

    mets = METS(...)
    sip = SIP.from_directory(
        directory_path="path/to/prepared/directory",
        mets=mets
    )
    sip.finalize(...)

Installation using Python Virtualenv for development purposes
-------------------------------------------------------------

You can install the application inside a virtualenv using the following
instructions.


Create a virtual environment::
    
    python3 -m venv venv

Run the following to activate the virtual environment::

    source venv/bin/activate

Install the required software with commands::

    pip install --upgrade pip==20.2.4 setuptools
    pip install -r requirements_github.txt
    pip install .

To deactivate the virtual environment, run ``deactivate``.
To reactivate it, run the ``source`` command above.

Copyright
---------
Copyright (C) 2023 CSC - IT Center for Science Ltd.

This program is free software: you can redistribute it and/or modify it under the terms
of the GNU Lesser General Public License as published by the Free Software Foundation, either
version 3 of the License, or (at your option) any later version.

This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY;
without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
See the GNU Lesser General Public License for more details.

You should have received a copy of the GNU Lesser General Public License along with
this program.  If not, see https://www.gnu.org/licenses/.
