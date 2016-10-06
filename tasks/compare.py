from invoke import task
import pandas

from .download import (read_downloaded_messages, update_audio_filenames,
                       label_branches)
from .settings import *

@task
def compare(ctx):
    """Compare acoustic similarity."""
    messages = read_downloaded_messages()
    update_audio_filenames(messages)
    branches = label_branches(messages)
    expanded = []
    for branch in branches.itertuples():
        expanded.append(_expand_message_list(branch))
    expanded = pandas.concat(expanded, ignore_index=True)
    labeled = (expanded.merge(messages)
                       .sort_values(['branch_id', 'generation'])
                       .reset_index(drop=True))
    acoustic_similarities = labeled.groupby('branch_id').apply(acoustic_similarity_chain)
    acoustic_similarities.to_csv(Path(DATA_DIR, 'similarities.csv'), index=False)


def expand_message_list(branch):
    expanded = pandas.DataFrame(dict(
        message_id=branch.message_list,
        branch_id=branch.branch_id
    ))
    return expanded


def acoustic_similarity_chain(sounds):
    mapping = create_mapping_from_chain(sounds.audio.tolist())
    return acousticsim.main.acoustic_similarity_mapping(mapping)


def create_mapping_from_chain(sounds):
    for i in range(len(sounds) - 1):
        yield (sounds[i], sounds[i+1])
