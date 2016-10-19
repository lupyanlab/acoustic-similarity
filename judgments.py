#!/usr/bin/env python
from datetime import datetime

from psychopy import visual, core, event, sound, logging
from unipath import Path
import pandas
import numpy

from tasks.util import get_linear_edges
from tasks.settings import *

DATA_DIR = Path(DATA_DIR, 'judgments')
if not DATA_DIR.isdir():
    DATA_DIR.mkdir()
DATA_FILE = Path(DATA_DIR, '{name}.csv')


class SimilarityJudgments(object):
    """Collect similarity judgments comparing two sounds.

    On each trial, participants hear two sounds played in sequence. After
    hearing the second sound, they rate the similarity between the sounds
    on a 7-point scale.

    Pressing 'q' during a trial causes the experiment to quit.

    If any of the recordings are unplayable or too short to hear, those edges
    will be skipped.
    """
    KEYBOARD = dict(q='quit')
    BUTTON_SIZE = 0.5
    DATA_COLS = 'name datetime sound_x sound_y rating'.split()
    DELAY = 0.5  # time between sounds

    def __init__(self, player, overwrite=False):
        self.player = player
        self.player['datetime'] = datetime.now()
        seed = self.player['datetime'].toordinal()
        fname = DATA_FILE.format(**self.player)
        fmode = 'w' if overwrite else 'a'
        self.data_file = open(fname, fmode)
        self.trials = make_trials(seed=seed, completed_csv=fname)

        self.win = visual.Window(units='pix')
        self.scale = RatingScale(self.win)
        self.KEYBOARD.update({str(i): i for i in self.scale.values})

        self.mouse = event.Mouse(win=self.win)
        self.sounds = {}

    def run(self):
        for block in self.trials:
            try:
                self.run_block(block)
            except QuitExperiment:
                logging.info("Quitting experiment")
                break
            else:
                self.break_screen()

        self.data_file.close()
        # sound.exit()
        # core.quit()

    def run_block(self, block):
        for trial in block:
            try:
                self.run_trial(trial)
            except BadRecording as e:
                logging.warning(e)
                continue

    def run_trial(self, trial):
        """
        Args:
            trial: namedtuple, e.g., from pandas.DataFrame.itertuples()
        """
        event.clearEvents()
        self.mouse.clickReset()

        try:
            self.load_sounds(trial.sound_x, trial.sound_y)
        except BadRecording as e:
            # Record that this trial was bad in the data before re-raising.
            self.write_trial(trial)
            raise e

        self.sound_x.play()
        core.wait(self.sound_x.getDuration() + self.DELAY)
        self.sound_y.play()
        core.wait(self.sound_y.getDuration())

        self.scale.draw()
        self.win.flip()
        response = self.check_keyboard()
        if response:
            self.write_trial(trial, response)

        self.win.flip()

    def break_screen(self):
        pass

    def load_sounds(self, sound_x_name, sound_y_name):
        """Load the sounds to compare on this trial.

        e.g. sets `self.sound_x = sound.Sound(sound_x_name)` but does it
        intelligently, only creating the sounds as necessary.
        """
        obj_name_pairs = zip(['sound_x', 'sound_y'],
                             [sound_x_name, sound_y_name])
        for (obj, name) in obj_name_pairs:
            snd = self.sounds.setdefault(name, sound.Sound(name))
            if snd.getDuration() < 1.0:
                raise BadRecording(name)
            setattr(self, obj, snd)

    def show_scale(self):
        # draw scale here
        self.win.flip()

    def check_keyboard(self):
        keyboard_responses = event.waitKeys(keyList=self.KEYBOARD.keys())
        key = self.KEYBOARD.get(keyboard_responses[0])
        if key == 'quit':
            logging.info('key press requested experiment quit')
            raise QuitExperiment
        response = dict(similarity=key)
        return response

    def write_trial(self, trial, response=None):
        data = self.player.copy()
        data.update(trial._asdict())
        if response:
            logging.info("Writing a response {}".format(response))
            data.update(response)
        row = [data.get(name, '') for name in self.DATA_COLS]
        self.data_file.write(','.join(map(str, row))+'\n')


def make_trials(seed=None, completed_csv=None):
    random = numpy.random.RandomState(seed)
    edges = get_linear_edges()
    unique = edges[['sound_x', 'sound_y']].drop_duplicates()

    try:
        previous_data = pandas.read_csv(completed_csv)
    except ValueError, IOError:
        logging.info('Couldn\'t find any previous data')
        trials = unique
    else:
        completed_edges = edges_to_sets(previous_data)
        is_unfinished = (pandas.Series(edges_to_sets(unique),
                                       index=unique.index)
                               .apply(lambda x: x not in completed_edges))
        trials = unique[is_unfinished]

    trials.insert(0, 'block_ix', random.choice(range(1,5), len(trials)))
    trials = (trials.sort_values('block_ix')
                    .reset_index(drop=True))
    trials.insert(0, 'trial_ix', range(1, len(trials)+1))

    blocks = [block.itertuples() for _, block in trials.groupby('block_ix')]
    return blocks


def edges_to_sets(edges):
    return [{edge.sound_x, edge.sound_y} for edge in edges.itertuples()]


class RatingScale(object):
    def __init__(self, win, **kwargs):
        self.values = range(1, 8)
        width = 500
        gutter = width/len(self.values)
        x_positions = numpy.array([gutter * i for i in self.values]) - width/2
        rating_kwargs = dict(win=win, **kwargs)
        self._ratings = [visual.TextStim(text=i, pos=(x, 0), **rating_kwargs)
                         for i, x in zip(self.values, x_positions)]
        labels = {1: 'Not at all', 7: 'Exact matches'}
        label_y = -20
        self._labels = [visual.TextStim(win, text=text,
                                        pos=(x_positions[x-1], label_y))
                        for x, text in labels.items()]

    def draw(self):
        for rating in self._ratings:
            rating.draw()
        for label in self._labels:
            label.draw()

def get_player_info():
    return dict(name='pierce')


class QuitExperiment(Exception):
    pass


class BadRecording(Exception):
    """The recording is not good enough to obtain similarity judgments from."""


if __name__ == '__main__':
    logging.console.setLevel(logging.INFO)
    player = get_player_info()
    judgments = SimilarityJudgments(player, overwrite=True)
    judgments.run()
