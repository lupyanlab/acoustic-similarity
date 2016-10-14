from datetime import datetime

from psychopy import visual, core, event, sound, logging
from unipath import Path

from tasks.data import get_linear_edges
from tasks.settings import *

DATA_DIR = Path(DATA_DIR, 'judgments')
if not DATA_DIR.isdir():
    DATA_DIR.mkdir()
DATA_FILE = Path(DATA_DIR, '{name}.csv')


class SimilarityJudgments(object):
    """Judge the similarity between two sounds.

    On each trial, two buttons are presented on the screen. Clicking on these
    buttons playes one of the sounds. A response scale is presented along the
    bottom of the screen. Players rate the two sounds on a 7-point scale.

    Pressing 'q' during a trial causes the experiment to quit.

    If any of the recordings are unplayable or too short to hear, those edges
    will be skipped.
    """
    KEYBOARD = dict(q='quit')
    KEYBOARD.update({str(i): i for i in range(1, 8)})
    BUTTON_SIZE = 0.5
    DATA_COLS = 'player datetime sound_x sound_y rating'

    def __init__(self, player):
        self.player = player
        self.data_file = open(DATA_FILE.format(**self.player), 'w')

        self.win = visual.Window()
        left, right = calculate_button_positions()
        button_kwargs = dict(win=self.win, lineColor='black',
                             width=self.BUTTON_SIZE, height=self.BUTTON_SIZE)
        self.sound_x_button = visual.Rect(pos=left, **button_kwargs)
        self.sound_y_button = visual.Rect(pos=right, **button_kwargs)
        self.edges = get_edges_to_judge()
        self.mouse = event.Mouse(win=self.win)

    def run(self):
        for edge in self.edges:
            try:
                self.run_trial(edge.sound_x, edge.sound_y)
            except BadRecording as e:
                logging.warning(e)
                continue
            except QuitExperiment:
                break
        core.quit()
        self.data_file.close()

    def run_trial(self, sound_x_name, sound_y_name):
        trial = dict(sound_x=sound_x_name, sound_y=sound_y_name)
        event.clearEvents()
        self.mouse.clickReset()

        try:
            self.load_sounds(sound_x_name, sound_y_name)
        except BadRecording as e:
            # Record that this trial was bad in the data before passing up.
            self.write_trial(trial)
            raise e
        self.show_trial()

        while True:
            self.check_mouse()
            response = self.check_keyboard()
            if response:
                self.write_trial(trial, response)
                break
            core.wait(0.1)

    def load_sounds(self, sound_x_name, sound_y_name):
        obj_pairs = zip(['sound_x', 'sound_y'], [sound_x_name, sound_y_name])
        for (name, obj) in name_obj_pairs:
            # ex: sets self.sound_x = sound.Sound(sound_x_name)
            setattr(self, obj, sound.Sound(name))
            if getattr(self, obj).getDuration() < 1.0:
                raise BadRecording(name)

    def show_screen(self):
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
                logging.info('Mouse press outside of buttons')

    def check_keyboard(self):
        response = dict(similarity='')

        keyboard_responses = event.getKeys(keyList=self.KEYBOARD.keys())

        if keyboard_responses:
            key = self.KEYBOARD.get(keyboard_responses[0])
            if key == 'quit':
                logging.info('key press requested experiment quit')
                raise QuitExperiment
            response['similarity'] = key

        return response


    def write_trial(self, trial, response):
        data = self.player
        data.update(trial)
        data.update(response)





def get_player_info():
    return dict(name='pierce')


def get_edges_to_judge():
    edges = get_linear_edges()
    unique_edges = edges[['sound_x', 'sound_y']].drop_duplicates()
    return unique_edges.iloc[:1].itertuples()


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
    judgments = SimilarityJudgments(player)
    judgments.run()
