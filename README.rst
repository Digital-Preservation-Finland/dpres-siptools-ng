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

See the `online documentation`_ and example code under ``doc/source/examples``.

.. _online documentation: https://digital-preservation-finland.github.io/dpres-siptools-ng

Installation using Python Virtualenv for development purposes
-------------------------------------------------------------

You can install the application inside a virtualenv using the following
instructions. This might require installing some C build tools.


Create a virtual environment::
    
    python3 -m venv venv

Run the following to activate the virtual environment::

    source venv/bin/activate

Install the required software with commands::

    pip install --upgrade pip setuptools
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
