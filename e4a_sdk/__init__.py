from .client import E4AClient, E4AError
__all__ = ["E4AClient", "E4AError"]
from core.__version__ import __version__

# Use the version in a way that satisfies the linter
version = __version__
