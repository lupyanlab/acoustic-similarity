from invoke import task
from .settings import *

@task
def compare(ctx):
    """Compare acoustic similarity."""


def acoustic_similarity_chain(sounds, **kwargs):
    mapping = create_mapping_from_chain(sounds)
    return acousticsim.main.acoustic_similarity_mapping(mapping)


def create_mapping_from_chain(sounds):
    for i in range(len(sounds) - 1):
        yield (sounds[i], sounds[i+1])
