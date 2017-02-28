import sys
import json

from invoke import task
import pandas
from acousticsim.main import acoustic_similarity_mapping

from .util import get_linear_edges, get_between_category_edges
from .settings import *


compare_sounds_help = dict(
    type=("Type of comparison. Provide `--type=list` to see available "
          "comparison types. Type determines how edges are computed "
          "before making the comparisons. "
          "If no type is given, all types are compared."),
    x=("Path to first wav file to compare. Optional."
       "If specified, arg y is required."),
    y="Path to second wav file. Optional.",
    json_kwargs="Key word args to pass to acoustic_similarity_mapping function",
)


@task(help=compare_sounds_help)
def compare_sounds(ctx, type=None, x=None, y=None, json_kwargs=None):
    """Compute acoustic similarity between .wav files.

    Run MFCC comparisons and return the distances:

        $ inv compare_sounds -j '{"rep": "mfcc", "num_coeffs": 12, "output_sim": true}'

    To see what other options are available via the json_kwargs argument,
    see:

        https://github.com/PhonologicalCorpusTools/CorpusTools/blob/master/corpustools/acousticsim/main.py#L48

    """
    kwargs = json.loads(json_kwargs) if json_kwargs else {}

    if x and y:
        edges = create_single_edge(x, y)
        similarities = calculate_similarities(edges, **kwargs)
        similarities.to_csv(sys.stdout, index=False)
        return
    elif x or y:
        raise AssertionError('need both -x and -y')

    available_types = ['linear', 'between']

    if type and type == 'list':
        print('Available comparisons:')
        for t in available_types:
            print('  - '+t)
        return

    if type:
        types = [type]
    else:
        types = available_types

    if 'linear' in types:
        edges = get_linear_edges()
        similarities = calculate_similarities(edges, **kwargs)
        similarities.to_csv(Path(DATA_DIR, 'linear.csv'), index=False)

    if 'between' in types:
        edges = get_between_category_edges(n_sample=100)
        similarities = calculate_similarities(edges, **kwargs)
        similarities.to_csv(Path(DATA_DIR, 'between.csv'), index=False)


def create_single_edge(x, y):
    x, y = find_sound(x), find_sound(y)
    return pandas.DataFrame(dict(sound_x=x, sound_y=y), index=[0])


def calculate_similarities(edges, **kwargs):
    unique_edges = edges[['sound_x', 'sound_y']].drop_duplicates()
    mapping = [(edge.sound_x, edge.sound_y)
               for edge in unique_edges.itertuples()]
    results = acoustic_similarity_mapping(mapping, **kwargs)
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
