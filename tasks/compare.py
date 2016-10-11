import sys
from invoke import task
import pandas
from acousticsim.main import acoustic_similarity_mapping

from .download import (read_downloaded_messages, update_audio_filenames,
                       label_branches)
from .settings import *


@task(help=dict(type=("Type of comparison. Right now only option is 'linear'. "
                      "If no type is given, all types are compared."),
                x=("Path to first wav file to compare. Optional."
                   "If specified, arg y is required."),
                y="Path to second wav file. Optional."))
def compare(ctx, type='linear', x=None, y=None):
    """Compare acoustic similarity."""
    if x and y:
        edges = create_single_edge(x, y)
        output = sys.stdout
    elif x or y:
        raise AssertionError('need both -x and -y')
    elif type == 'linear':
        edges = get_linear_edges()
        output = Path(DATA_DIR, 'linear.csv')
    else:
        raise NotImplementedError('type == {}'.format(type))

    similarities = calculate_similarities(edges)
    similarities.to_csv(output, index=False)


def create_single_edge(x, y):
    x, y = find_sound(x), find_sound(y)
    return pandas.DataFrame(dict(sound_x=x, sound_y=y), index=[0])


def get_linear_edges(branches=None):
    if branches is None:
        branches = get_messages_by_branch()
        branches = branches.ix[branches.generation > 0]

    def _get_linear_edges(branch):
        sounds = branch.audio.tolist()
        edges = []
        for i in range(len(sounds) - 1):
            edges.append((sounds[i], sounds[i+1]))
        return pandas.DataFrame.from_records(edges,
                                             columns=['sound_x', 'sound_y'])

    if 'branch_id' in branches:
        edges = branches.groupby('branch_id').apply(_get_linear_edges)
        edges = edges.reset_index(level=0).reset_index(drop=True)
    else:
        edges = _get_linear_edges(branches)
    return edges


def get_messages_by_branch():
    messages = read_downloaded_messages()
    update_audio_filenames(messages)
    branches = label_branches(messages)
    expanded = [expand_message_list(branch) for branch in branches.itertuples()]
    labeled = (pandas.concat(expanded, ignore_index=True)
                     .merge(messages))
    labeled = (labeled.sort_values(['branch_id', 'generation'])
                      .reset_index(drop=True))
    return labeled


def expand_message_list(branch):
    expanded = pandas.DataFrame(dict(
        message_id=branch.message_list,
        branch_id=branch.branch_id
    ))
    return expanded


def calculate_similarities(edges):
    unique_edges = edges[['sound_x', 'sound_y']].drop_duplicates()
    mapping = [(edge.sound_x, edge.sound_y)
               for edge in unique_edges.itertuples()]
    results = acoustic_similarity_mapping(mapping)
    records = [(x, y, score) for (x, y), score in results.items()]
    cols = ['sound_x', 'sound_y', 'similarity']
    scored_edges = pandas.DataFrame.from_records(records, columns=cols)

    # The sound_x, sound_y output from acousticsim is the basename of the file,
    # whereas the sound_x, sound_y of the input are full paths.
    # Here I'm normalizing sound_x and sound_y to both be type message_id
    # before merging the scores back with the original edges.
    edges['sound_x'] = edges.sound_x.apply(message_id_from_wav)
    edges['sound_y'] = edges.sound_y.apply(message_id_from_wav)
    scored_edges['sound_x'] = scored_edges.sound_x.apply(message_id_from_wav)
    scored_edges['sound_y'] = scored_edges.sound_y.apply(message_id_from_wav)
    labeled = edges.merge(scored_edges)

    return labeled


def message_id_from_wav(x):
    name = Path(x).stem
    try:
        return int(name)
    except ValueError:
        return name


def find_sound(x):
    if Path(x).exists():
        return x
    else:
        shortname = '{sounds_dir}/{x}.wav'
        return shortname.format(sounds_dir=SOUNDS_DIR, x=x)
