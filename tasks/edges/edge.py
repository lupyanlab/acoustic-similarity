import pandas
from unipath import Path

from ..settings import SOUNDS_DIR

def create_single_edge(x, y):
    x, y = find_sound(x), find_sound(y)
    return pandas.DataFrame(dict(sound_x=x, sound_y=y), index=[0])


def find_sound(x):
    if Path(x).exists():
        return x
    else:
        shortname = '{sounds_dir}/{x}.wav'
        return shortname.format(sounds_dir=SOUNDS_DIR, x=x)


def create_edge_set(frame):
    frame.copy()
    frame['edge_set'] = [frozenset({r.sound_x, r.sound_y})
                         for r in frame.itertuples()]
    return frame
