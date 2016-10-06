from invoke import task
import pandas

from .download import _read_downloaded_messages, _label_branches
from .settings import *

@task
def compare(ctx):
    """Compare acoustic similarity."""
    messages = _read_downloaded_messages()
    branches = _label_branches(messages)
    branches.apply(_expand_message_list)


def _expand_message_list(branch):
    expanded = pandas.DataFrame(dict(
        message_id=branch.message_list,
        branch_id=branch.branch_id
    ))
    return expanded


def acoustic_similarity_chain(sounds, **kwargs):
    mapping = create_mapping_from_chain(sounds)
    return acousticsim.main.acoustic_similarity_mapping(mapping)


def _create_mapping_from_chain(sounds):
    for i in range(len(sounds) - 1):
        yield (sounds[i], sounds[i+1])
