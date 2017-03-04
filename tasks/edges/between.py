import itertools

import pandas
import numpy

from .messages import read_downloaded_messages, update_audio_filenames


def get_all_between_edges(messages=None, n_sample=10, seed=None):
    # between_category_edges = get_between_category_edges()
    fixed_edges = get_between_category_fixed_edges()
    # consecutive_edges = get_between_category_consecutive_edges()

    between_edges = pandas.concat(
        [fixed_edges],
        ignore_index=True
    )
    between_edges['edge_set'] = [frozenset({r.sound_x, r.sound_y})
                                 for r in between_edges.itertuples()]
    between_edges.drop_duplicates(subset='edge_set', inplace=True)
    del between_edges['edge_set']
    return between_edges


# def get_between_category_edges():
#     messages = read_downloaded_messages()
#     messages = update_audio_filenames(messages)
#     messages = messages.ix[(messages.generation > 0) & (~messages.rejected)]
#     edges = get_between_combinations(messages)
#     return pandas.DataFrame.from_records(edges, columns=['sound_x', 'sound_y'])


def get_between_category_fixed_edges():
    messages = read_downloaded_messages()
    messages = update_audio_filenames(messages)
    messages = messages.ix[(messages.generation > 0) & (~messages.rejected)]
    edges = messages.groupby('generation').apply(get_between_combinations)
    return edges


def get_between_combinations(messages):
    category_names = messages.category.unique()
    edges = []
    for target in category_names:
        matches = messages.ix[messages.category == target, 'audio']
        mismatches = messages.ix[messages.category != target, 'audio']
        edges.extend(list(itertools.product(matches, mismatches)))
    return pandas.DataFrame(edges, columns=['sound_x', 'sound_y'])
