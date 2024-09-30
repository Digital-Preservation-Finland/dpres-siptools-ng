Frequently asked questions
==========================

Questions and answers concerning the siptools-ng.

For questions regarding the digital preservation service as a whole, see
`the FAQ section on the official site <https://dpres.fi/support/faq>`_ (in Finnish).

My SIP was rejected due to a missing dmdSec section in mets.xml. What do I need to do?
--------------------------------------------------------------------------------------

The national METS schema requires a `dmdSec` section in the METS schema.
This means you **need to add descriptive metadata** to your SIP.

See :ref:`add_descriptive_metadata` for details.

The files have wrong technical metadata! How can I ensure they're correct?
--------------------------------------------------------------------------

You can give :meth:`siptools_ng.file.File.generate_technical_metadata` additional parameters
to ensure file-scraper generates the correct technical metadata.

See :ref:`generating_technical_metadata` for more details.

I want to check or modify the METS document. Can I do that?
-----------------------------------------------------------

Yes, the METS object is accessible through the :attr:`siptools_ng.sip.SIP.mets` property.
Please check :class:`mets_builder.mets.METS` for available methods and properties.

Most functionality under `METS` can be used, although it's not advised to add
digital objects manually as they won't be tracked by siptools-ng.

What is dpres-siptools? Why should I use dpres-siptools-ng instead of dpres-siptools?
-------------------------------------------------------------------------------------

dpres-siptools is the command-line toolset for creating SIPs. dpres-siptools
**is deprecated** and has been replaced with dpres-siptools-ng.

dpres-siptools was designed around a set of command-line tools meant to be executed
in a predetermined sequence. This approach came with various drawbacks:

* Commands have to be executed in a rigid order
* There is no way to inspect the incomplete SIP before creating the final SIP
  file
* dpres-siptools relies on state files stored on disk and numerous command
  calls, which made it scale poorly on larger SIPs
* The Python API was implemented after the fact in an ad-hoc manner around the
  command-line tools themselves and was rigid in much the same way

dpres-siptools-ng was implemented from scratch and designed around an
object-oriented API and a class hierarchy that resembles the final SIP and its
contents.

While dpres-siptools-ng does not currently provide a command-line toolset like
dpres-siptools, one can be implemented if there is demand for it.


