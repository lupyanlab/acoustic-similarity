from datetime import datetime

from psychopy import visual, core, event, sound, logging
from unipath import Path
import pandas

from tasks.util import get_linear_edges
from tasks.settings import *

DATA_DIR = Path(DATA_DIR, 'judgments')
if not DATA_DIR.isdir():
    DATA_DIR.mkdir()
DATA_FILE = Path(DATA_DIR, '{name}.csv')


class SimilarityJudgments(object):
    """Collect similarity judgments comparing two sounds.

    On each trial, two buttons are presented on the screen. Clicking on these
    buttons plays one of the sounds. A response scale is presented along the
    bottom of the screen. Players rate the sounds on a 7-point scale.

    Pressing 'q' during a trial causes the experiment to quit.

    If any of the recordings are unplayable or too short to hear, those edges
    will be skipped.
    """
    KEYBOARD = dict(q='quit')
    KEYBOARD.update({str(i): i for i in range(1, 8)})
    BUTTON_SIZE = 0.5
    DATA_COLS = 'name datetime sound_x sound_y rating'.split()

    def __init__(self, player, overwrite=False):
        self.player = player
        self.player['datetime'] = datetime.now()
        seed = self.player['datetime'].toordinal()
        fname = DATA_FILE.format(**self.player)
        fmode = 'w' if overwrite else 'a'
        self.data_file = open(fname, fmode)

        self.win = visual.Window()
        left, right = calculate_button_positions()
        button_kwargs = dict(win=self.win, lineColor='black',
                             width=self.BUTTON_SIZE, height=self.BUTTON_SIZE)
        self.sound_x_button = visual.Rect(pos=left, **button_kwargs)
        self.sound_y_button = visual.Rect(pos=right, **button_kwargs)
        self.edges = get_edges_to_judge(seed, completed_csv=fname)
        self.mouse = event.Mouse(win=self.win)
        self.sounds = {}

    def run(self):
        for edge in self.edges:
            try:
                self.run_trial(edge.sound_x, edge.sound_y)
            except BadRecording as e:
                logging.warning(e)
                continue
            except QuitExperiment:
                logging.info("Quitting experiment")
                break

        logging.info("Finishing experiment")
        self.data_file.close()
        #sound.exit()
        #core.quit()

    def run_trial(self, sound_x_name, sound_y_name):
        trial = dict(sound_x=sound_x_name, sound_y=sound_y_name)
        event.clearEvents()
        self.mouse.clickReset()

        try:
            self.load_sounds(sound_x_name, sound_y_name)
        except BadRecording as e:
            # Record that this trial was bad in the data before re-raising.
            self.write_trial(trial)
            raise e
        self.show_trial()

        while True:
            self.check_mouse()
            response = self.check_keyboard()
            if response:
                logging.info('Caught a response')
                self.write_trial(trial, response)
                break
            core.wait(0.1)

        logging.info('Finished running trial')

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

    def show_trial(self):
        self.sound_x_button.draw()
        self.sound_y_button.draw()
        self.win.flip()

    def check_mouse(self):
        mouse_responses = self.mouse.getPressed()

        if mouse_responses and any(mouse_responses):
            pos = self.mouse.getPos()
            if self.sound_x_button.contains(pos):
                self.sound_x.play()
            elif self.sound_y_button.contains(pos):
                self.sound_y.play()
            else:
                logging.info('Mouse pressed outside of buttons')

    def check_keyboard(self):
        response = None
        keyboard_responses = event.getKeys(keyList=self.KEYBOARD.keys())

        if keyboard_responses:
            key = self.KEYBOARD.get(keyboard_responses[0])
            if key == 'quit':
                logging.info('key press requested experiment quit')
                raise QuitExperiment
            response = dict(similarity=key)

        return response

    def write_trial(self, trial, response=None):
        data = self.player.copy()
        data.update(trial)
        if response:
            logging.info("Writing a response {}".format(response))
            data.update(response)
        row = [data.get(name, '') for name in self.DATA_COLS]
        self.data_file.write(','.join(map(str, row))+'\n')


def get_player_info():
    return dict(name='pierce')


def get_edges_to_judge(seed=None, completed_csv=None):
    edges = get_linear_edges()
    unique = edges[['sound_x', 'sound_y']].drop_duplicates()

    try:
        previous_data = pandas.read_csv(completed_csv)
    except ValueError, IOError:
        logging.info('Couldn\'t find any previous data')
        unfinished = unique
    else:
        completed_edges = edges_to_sets(previous_data)
        is_unfinished = (pandas.Series(edges_to_sets(unique),
                                       index=unique.index)
                               .apply(lambda x: x not in completed_edges))
        unfinished = unique[is_unfinished]

    shuffled = (unfinished.sample(len(unique), random_state=seed)
                          .reset_index(drop=True))
    return shuffled.iloc[:10].itertuples()


def edges_to_sets(edges):
    return [{edge.sound_x, edge.sound_y} for edge in edges.itertuples()]


def calculate_button_positions():
    gutter = 0.5
    height = 0
    left = (-gutter, height)
    right = (gutter, height)
    return left, right


class QuitExperiment(Exception):
    pass

class BadRecording(Exception):
    """The recording is not good enough to obtain similarity judgments from."""

if __name__ == '__main__':
    logging.console.setLevel(logging.INFO)
    player = get_player_info()
    judgments = SimilarityJudgments(player, overwrite=True)
    judgments.run()