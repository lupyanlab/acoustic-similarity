# Import invoke tasks to run from the command line.
#
# Warning! Failed imports are ignored. This allows portability
# of some functions across environments.
import logging

logger = logging.getLogger(__name__)
logger.addHandler(logging.StreamHandler())

from .download import download, create_edges_for_judgments
from .compare_sounds import compare_sounds, edge_types
from .compare_words import compare_words
