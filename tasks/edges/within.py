import itertools
import pandas
import numpy

from .messages import read_downloaded_messages, update_audio_filenames


def get_within_edges(messages=None, n_sample=None):
    rand = numpy.random.RandomState()

    if messages is None:
        messages = read_downloaded_messages()
        update_audio_filenames(messages)

    edges = []
    for category_name, messages in messages.groupby('category'):
        category_messages = messages.audio.tolist()
        all_message_pairs = itertools.combinations(category_messages, 2)
        message_pairs = [(x, y) for x, y in all_message_pairs
                         if x != y]

        rand.shuffle(message_pairs)
        n_sample = n_sample or len(message_pairs)

        for sound_x, sound_y in message_pairs[:n_sample]:
            edges.append(dict(sound_x=sound_x, sound_y=sound_y))

    return pandas.DataFrame.from_records(edges)
