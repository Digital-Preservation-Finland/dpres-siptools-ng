**NOTE: The project is not ready for production use. It is published prematurely to give an opportunity to get acquainted with the project in advance and to get feedback.**

To give feedback, please open a GitHub issue or pull request.

dpres-siptools-ng
=================

Library for creating Submission Information Packages (SIP) that comply to the specifications of national digital preservation services of Finland.

Installation
-----------
Installation requires Python 3.6 or newer. The software has been tested using
CentOS 7.

You can install the application inside a virtualenv using the following
instructions.

To create a virtualenv, activate it and install dependencies as well as the package itself, run::

    python3 -m venv venv
    source venv/bin/activate
    pip install --upgrade pip setuptools
    pip install -r requirements_dev.txt
    pip install .

To deactivate the virtualenv, run ``deactivate``. The created virtualenv needs
to be active in order to use dpres-siptools-ng.

To use siptools-ng you will also have to install file-scraper and it's dependencies. See https://github.com/Digital-Preservation-Finland/file-scraper for instructions.

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

See the usage documentation of ``dpres-mets-builder`` for instructions to build a ``METS`` object (replacing digital object handling with ``SIPDigitalObject``), and turn it into a SIP with the following commands::

    from siptools_ng.sip import SIP

    sip = SIP(mets=mets)
    sip.finalize(
        output_filepath="sip.tar",
        sign_key_filepath="rsa-keys.crt"
    )

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
