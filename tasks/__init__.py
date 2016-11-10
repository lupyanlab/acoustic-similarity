# Import invoke tasks to run from the command line.
#
# Warning! Failed imports are ignored. This allows portability
# of some functions across environments.
from __future__ import print_function
import logging

logger = logging.getLogger(__name__)
logger.addHandler(logging.StreamHandler())

import_error_msg = 'failed to import task: "{}"'

try:
    from .download import download
    from .compare_sounds import compare_sounds
    from .compare_words import compare_words
except ImportError:
    print('failed to import tasks')
