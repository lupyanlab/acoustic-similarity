import itertools

import pandas
import numpy

from .messages import read_downloaded_messages, update_audio_filenames


def get_all_between_edges(messages=None, n_sample=10, seed=None):
    # between_category_edges = get_between_category_edges()
    fixed_edges = get_between_category_fixed_edges()
    consecutive_edges = get_between_category_consecutive_edges()

    between_edges = pandas.concat(
        [fixed_edges, consecutive_edges],
        ignore_index=True
    )
    between_edges = remove_duplicate_edges(between_edges)
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
    edges = remove_duplicate_edges(edges)
    return edges


def get_between_category_consecutive_edges():
    messages = read_downloaded_messages()
    messages = update_audio_filenames(messages)
    messages = messages.ix[(messages.generation > 0) & (~messages.rejected)]

    edges = []
    for (category, generation), current_generation in \
            messages.groupby(['category', 'generation']):

        if generation == max(messages.generation):
            break

        target_audio = current_generation.audio
        next_gen_not_target = (messages.generation == generation+1) &\
                              (messages.category != category)
        next_generation = messages.ix[next_gen_not_target, 'audio']
        edges.extend(list(itertools.product(target_audio, next_generation)))
    edges = pandas.DataFrame(edges, columns=['sound_x', 'sound_y'])
    edges = remove_duplicate_edges(edges)
    return edges


def get_between_combinations(messages):
    category_names = messages.category.unique()
    edges = []
    for target in category_names:
        matches = messages.ix[messages.category == target, 'audio']
        mismatches = messages.ix[messages.category != target, 'audio']
        edges.extend(list(itertools.product(matches, mismatches)))
    return pandas.DataFrame(edges, columns=['sound_x', 'sound_y'])


def remove_duplicate_edges(frame):
    frame = frame.copy()
    frame['edge_set'] = [frozenset({r.sound_x, r.sound_y})
                         for r in frame.itertuples()]
    frame.drop_duplicates(subset='edge_set', inplace=True)
    del frame['edge_set']
    return frame
