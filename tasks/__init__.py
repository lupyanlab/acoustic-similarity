from invoke import task, run, Collection
import acousticsim

from .download import download


@task
def compare(ctx, edges_csv=None):
    """Compare acoustic similarity."""


def acoustic_similarity_chain(sounds, **kwargs):
    mapping = create_mapping_from_chain(sounds)
    return acousticsim.main.acoustic_similarity_mapping(mapping)


def create_mapping_from_chain(sounds):
    for i in range(len(sounds) - 1):
        yield (sounds[i], sounds[i+1])
