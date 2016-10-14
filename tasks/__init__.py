# Import invoke tasks to run from the command line.
#
# Warning! Failed imports are ignored. This allows portability
# of some functions across environments.

from __future__ import print_function

import_error_msg = 'failed to import task: "{}"'

try:
    from .download import download
except ImportError:
    print(import_error_msg.format('download'))

try:
    from .compare_sounds import compare_sounds
except ImportError:
    print(import_error_msg.format('compare_sounds'))
