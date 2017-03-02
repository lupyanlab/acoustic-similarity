import itertools
import pandas
import numpy

from .messages import (read_downloaded_messages, update_audio_filenames,
                       get_messages_by_branch, label_seed_id)


def get_all_within_edges():
    within_chain = get_within_chain_edges()
    within_seed = get_within_seed_edges()
    within_category = get_within_category_edges()

    within_edges = pandas.concat([within_chain, within_seed, within_category],
                                 ignore_index=True)
    within_edges['edge_set'] = [frozenset({r.sound_x, r.sound_y})
                                for r in within_edges.itertuples()]
    within_edges.drop_duplicates(subset='edge_set', inplace=True)
    del within_edges['edge_set']
    return within_edges


def get_within_chain_edges():
    branches = get_messages_by_branch()
    branches = branches.ix[(branches.generation > 0) & (~branches.rejected)]
    edges = branches.groupby('branch_id').apply(get_combinations)
    return edges


def get_within_seed_edges():
    messages = read_downloaded_messages()
    messages = update_audio_filenames(messages)
    messages = label_seed_id(messages)
    messages = messages.ix[(messages.generation > 0) & (~messages.rejected)]
    edges = messages.groupby('seed_id').apply(get_combinations)
    return edges


def get_within_category_edges():
    messages = read_downloaded_messages()
    messages = update_audio_filenames(messages)
    messages = messages.ix[(messages.generation > 0) & (~messages.rejected)]
    edges = messages.groupby('category').apply(get_combinations)
    return edges


def get_combinations(messages):
    """Given some messages, make all possible edges from it."""
    audio = messages.audio.tolist()
    pairs = list(itertools.combinations(audio, 2))
    return pandas.DataFrame(pairs, columns=['sound_x', 'sound_y'])
