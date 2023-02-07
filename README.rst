dpres-siptools-ng
==================================================================

Library for creating Submission Information Packages (SIP) that comply to the specifications of national digital preservation services of Finland.

Installation
-----------
Installation requires Python 3.6 or newer. The software has been tested using
CentOS 7.

You can install the application inside a virtualenv using the following
instructions.

To create a virtualenv, activate it and install dependencies as well as the package itself, run

::
    python3 -m venv venv
    source venv/bin/activate
    pip install --upgrade pip setuptools
    pip install -r requirements_dev.txt
    pip install .

To deactivate the virtualenv, run ``deactivate``. The created virtualenv needs
to be active in order to use dpres-siptools-ng.

Usage
-----
TODO: Add some examples how to use the project.

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
