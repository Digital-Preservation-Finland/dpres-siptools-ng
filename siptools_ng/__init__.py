try:
    from ._version import version as __version__
except ImportError:
    # Package not installed, provide something
    __version__ = "N/A"
