#!/usr/bin/env python
from datetime import datetime

from psychopy import visual, core, event, sound, logging
from unipath import Path
import pandas
import numpy

from tasks.util import *
from tasks.settings import *


class SimilarityJudgments(object):
    """Collect similarity judgments comparing two sounds.

    On each trial, participants hear two sounds played in sequence. After
    hearing the second sound, they rate the similarity between the sounds
    on a 7-point scale.

    Pressing 'q' during a trial causes the experiment to quit.
    """
    DATA_COLS = 'name datetime block_ix trial_ix sound_x sound_y reversed category similarity'.split()
    DATA_DIR = Path(DATA_DIR, 'judgments')
    if not DATA_DIR.isdir():
        DATA_DIR.mkdir()
    DATA_FILE = Path(DATA_DIR, '{name}.csv')

    DELAY = 0.5  # time between sounds

    def __init__(self, player, overwrite=False):
        self.session = player.copy()
        start_time = datetime.now()
        self.session['datetime'] = start_time
        seed = start_time.toordinal()

        fname = self.DATA_FILE.format(**player)
        fmode = 'w' if overwrite else 'a'
        self.data_file = open(fname, fmode)
        self.write_trial()

        # Make the trials for this participant.
        self.trial_blocks = make_trial_blocks(seed=seed, completed_csv=fname)

        # Create the trial objects.
        self.win = visual.Window(units='pix')
        self.scale = RatingScale(self.win)
        self.sounds = {}
        self.icon = visual.ImageStim(self.win, 'stimuli/speaker_icon.png')

    def run(self):
        """Run the experiment."""
        self.show_instructions()

        for block in self.trial_blocks:
            try:
                self.run_block(block)
            except QuitExperiment:
                break
            else:
                self.show_break_screen()

        self.data_file.close()
        core.quit()

    def run_block(self, block):
        """Run a block of trials."""
        for trial in block:
            self.run_trial(trial)

    def run_trial(self, trial):
        """Run a single trial."""
        first, second = self.get_or_create_sounds(trial.sound_x, trial.sound_y)
        if trial.reversed:
            first, second = second, first

        self.win.flip()
        event.clearEvents()

        self.play_and_wait(first)
        core.wait(self.DELAY)
        self.play_and_wait(second)
        self.scale.draw(flip=True)
        response = self.scale.get_response()

        response.update(**trial._asdict())
        self.write_trial(**response)

    def show_instructions(self):
        pass

    def break_screen(self):
        pass

    def get_or_create_sounds(self, *args):
        """Get sounds by name or create them if they don't exist."""
        return [self.sounds.setdefault(name, sound.Sound(name))
                for name in args]

    def play_and_wait(self, snd):
        duration = snd.getDuration()
        snd.play()
        self.icon.draw()
        self.win.flip()
        core.wait(duration)
        self.win.flip()

    def write_trial(self, **trial_data):
        data = self.session.copy()
        if trial_data:
            data.update(trial_data)
            row = []
            for name in self.DATA_COLS:
                value = data.get(name, '')
                if not value:
                    logging.warning('Data for col {} not found'.format(name))
                row.append(value)

            for x in trial_data.keys():
                if x not in self.DATA_COLS:
                    logging.warning('Data for {} not saved'.format(x))
        else:
            row = self.DATA_COLS
        self.data_file.write(','.join(map(str, row))+'\n')


def make_trial_blocks(seed=None, completed_csv=None):
    # Start with info for (gen i, gen i + 1) edges.
    edges = get_linear_edges()
    unique = edges[['sound_x', 'sound_y']].drop_duplicates()

    try:
        previous_data = pandas.read_csv(completed_csv)
        completed_edges = edges_to_sets(previous_data)
    except ValueError, IOError:
        trials = unique  # all trials are new
    else:
        is_unfinished = (pandas.Series(edges_to_sets(unique),
                                       index=unique.index)
                               .apply(lambda x: x not in completed_edges))
        trials = unique[is_unfinished]

    trials = unique.copy()
    random = numpy.random.RandomState(seed)
    trials.insert(0, 'block_ix', random.choice(range(1,5), len(trials)))
    trials = (trials.sort_values('block_ix')
                    .reset_index(drop=True))
    trials.insert(0, 'trial_ix', range(1, len(trials)+1))

    trials['reversed'] = random.choice(range(2), len(trials))
    trials['category'] = determine_imitation_category(trials.sound_x)
    # Assumes that sound_x and sound_y come from the same category!

    blocks = [block.itertuples() for _, block in trials.groupby('category')]
    random.shuffle(blocks)

    return blocks


def edges_to_sets(edges):
    return [{edge.sound_x, edge.sound_y} for edge in edges.itertuples()]


def determine_imitation_category(audio):
    messages = read_downloaded_messages()
    update_audio_filenames(messages)
    categories = messages[['audio', 'category']]
    categories.set_index('audio', inplace=True)
    return categories.reindex(audio).category.tolist()


class RatingScale(object):
    VALUES = range(1, 8)
    KEYBOARD = dict(q='quit')
    KEYBOARD.update({str(i): i for i in VALUES})
    X_GUTTER = 40
    FONT_SIZE = 30
    HIGHLIGHT_TIME = 0.5

    def __init__(self, win):
        self.win = win

        x_positions = numpy.array([(i-1) * self.X_GUTTER for i in self.VALUES])
        x_positions = x_positions - x_positions.mean()
        assert x_positions.max() < win.size[0]/2, "some ratings will be hidden"

        # Create text stim objects for all values of the scale
        rating_kwargs = dict(win=self.win, font='Consolas',
                             height=self.FONT_SIZE)
        self.ratings = [visual.TextStim(text=i, pos=(x, 0), **rating_kwargs)
                        for i, x in zip(self.VALUES, x_positions)]

        # Label some of the scale points
        label_names = {1: 'Not at all', 7: 'Exact matches'}
        label_y = -20
        self.labels = [visual.TextStim(self.win, text=text,
                                       pos=(x_positions[x-1], label_y))
                        for x, text in label_names.items()]

    def draw(self, flip=True):
        for rating in self.ratings:
            rating.draw()
        for label in self.labels:
            label.draw()

        if flip:
            self.win.flip()

    def get_response(self):
        keyboard_responses = event.waitKeys(keyList=self.KEYBOARD.keys())
        key = self.KEYBOARD.get(keyboard_responses[0])
        if key == 'quit':
            raise QuitExperiment
        self.highlight(key)
        return dict(similarity=key)

    def highlight(self, key):
        selected = self.ratings[int(key)-1]
        selected.setColor('green')
        self.draw()
        core.wait(self.HIGHLIGHT_TIME)
        selected.setColor('white')



def get_player_info():
    return dict(name='pierce')


class QuitExperiment(Exception):
    pass


class BadRecording(Exception):
    pass


if __name__ == '__main__':
    logging.console.setLevel(logging.WARNING)
    player = get_player_info()
    judgments = SimilarityJudgments(player, overwrite=True)
    judgments.run()
