import pandas
import numpy

from .messages import read_downloaded_messages, update_audio_filenames


def get_between_edges(messages=None, n_sample=10):
    if messages is None:
        messages = read_downloaded_messages()
        update_audio_filenames(messages)

    category_names = messages.category.unique()
    grouped_messages = messages.groupby('category')
    categories = {name: grouped_messages.get_group(name)
                  for name in category_names}

    rand = numpy.random.RandomState()

    edges = []
    for name in category_names:
        options = list(category_names)
        options.remove(name)
        for _ in range(n_sample):
            sampled_category = rand.choice(options)
            sound_x = rand.choice(categories[name].audio)
            sound_y = rand.choice(categories[sampled_category].audio)
            edges.append(dict(sound_x=sound_x, sound_y=sound_y))

    return pandas.DataFrame.from_records(edges)
