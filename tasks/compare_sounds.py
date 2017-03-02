import sys
import json

from invoke import task
import pandas
from acousticsim.main import acoustic_similarity_mapping

from .edges import (create_single_edge, get_linear_edges,
                    get_between_edges, get_all_within_edges,
                    message_id_from_wav)
from .settings import *


@task(help=dict(
    type="Type of comparison. Provide --type=list to see available comparison types. Type determines which edges are compared. If no type is given, all types are compared",
    x="Path to first wav file to compare. Optional. If specified, arg y is required.",
    y="Path to second wav file. Optional.",
    json_kwargs="Key word args to pass to acoustic_similarity_mapping function",
))
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

    available_types = ['linear', 'between', 'within']

    if type and type == 'list':
        print('Available comparisons:')
        for t in available_types:
            print('  - '+t)
        return

    if type:
        types = [type]
    else:
        types = available_types

    for edge_type in types:
        if edge_type == 'linear':
            edges = get_linear_edges()
        elif edge_type == 'between':
            edges = get_between_edges(n_sample=100)
        elif edge_type == 'within':
            edges = get_all_within_edges()
        else:
            raise NotImplementedError('edge type "{}"'.format(edge_type))

        similarities = calculate_similarities(edges, **kwargs)
        similarities.to_csv(Path(DATA_DIR, '{}.csv'.format(edge_type)),
                            index=False)


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
