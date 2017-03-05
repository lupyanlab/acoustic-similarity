#!/usr/bin/env python
from datetime import datetime
import webbrowser
import string

from psychopy import visual, core, event, sound, logging, gui
from unipath import Path
import pandas
import numpy

DATA_DIR = Path('../data/judgments')

TITLE = "Judge the similarity between two sounds"
INSTRUCTIONS = """\
On each trial, you will hear two sounds played in succession. To help you distinguish them, during the first you will see the number 1, and during the second a number 2. After hearing the second sound, you will be asked to rate how similar the two sounds are on a 7-point scale.

A 7 means the sounds are nearly identical. That is, if you were to hear these two sounds played again, you would likely be unable to tell whether they were in the same or different order as the first time you heard them. A 1 on the scale means the sounds are entirely different and you would never confuse them. Each sound in the pair will come from a different speaker, so try to ignore differences due to just people having different voices. For example, a man and a woman saying the same word should get a high rating.

Please try to use as much of the scale as you can while maximizing the likelihood that if you did this again, you would reach the same judgments. If you need to hear the sounds again, you can press 'r' to repeat the trial. If one of the sounds is a non-verbal sound (like someone tapping on the mic), or if you only hear a single sound, or if you are otherwise unable to judge the similarity between the sounds, press the 'e' key to report the error. Pressing 'q' will quit the experiment. Your progress will be saved and you can continue later. Press the SPACEBAR to begin the experiment.
"""

BREAK = "Take a short break. Take the headphones off, stand up, and stretch out. When you are ready to continue, press the SPACEBAR."

ERROR_FORM_TITLE = "Describe why you were unable to judge the similarity between the sounds. Type your response, and don't worry about capitalization or punctuation. For example, 'couldnt hear first sound' or 'second sound was not a voice'. When you are finished, press 'enter'."


class SimilarityJudgments(object):
    """Collect similarity judgments comparing two sounds."""
    DATA_COLS = ('name datetime block_ix trial_ix sound_x sound_y '
                 'reversed category similarity notes repeat').split()
    DATA_DIR = Path(DATA_DIR, 'judgments')
    if not DATA_DIR.isdir():
        DATA_DIR.mkdir()
    DATA_FILE = Path(DATA_DIR, '{name}.csv')

    PRE_DELAY = 0.5
    BETWEEN_DELAY = 0.8  # time between sounds

    def __init__(self, player, overwrite=False):
        self.session = player.copy()
        start_time = datetime.now()
        self.session['datetime'] = start_time
        seed = start_time.toordinal()

        fname = self.DATA_FILE.format(**player)
        fmode = 'w' if overwrite else 'a'
        write_header = ((not Path(fname).exists()) or fmode == 'w')
        self.data_file = open(fname, fmode, 0)
        if write_header:
            self.write_trial()

        # Make the trials for this participant.
        self.trials = Trials(seed=seed, completed_csv=fname)

        # Create the trial objects.
        self.win = visual.Window(fullscr=True, units='pix', allowGUI=False)
        self.text_kwargs = dict(win=self.win, font='Consolas',
                                wrapWidth=self.win.size[0] * 0.7)
        self.scale = RatingScale(self.text_kwargs)
        self.form = TextEntryForm(self.text_kwargs)
        self.sounds = {}
        self.icon = visual.ImageStim(self.win, 'stimuli/speaker_icon.png')
        self.icon_label = visual.TextStim(pos=(0, 110), color="black",
                                          height=50, **self.text_kwargs)

    def run(self):
        """Run the experiment."""
        self.show_instructions()

        for block in self.trials.blocks():
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
            while True:
                try:
                    self.run_trial(trial)
                except RepeatTrial:
                    pass
                else:
                    break


    def run_trial(self, trial):
        """Run a single trial."""
        first, second = self.get_or_create_sounds(trial.sound_x, trial.sound_y)
        if trial.reversed:
            first, second = second, first

        self.win.flip()
        event.clearEvents()

        core.wait(self.PRE_DELAY)
        self.play_and_wait(first, '1')
        core.wait(self.BETWEEN_DELAY)
        self.play_and_wait(second, '2')
        self.scale.draw(flip=True)

        response = dict(similarity=-1, notes='None', repeat=0)
        response.update(**trial._asdict())

        try:
            response['similarity'] = self.scale.get_response()
        except ReportError:
            response['notes'] = self.form.get_response()
        except RepeatTrial:
            response['repeat'] = 1
            self.write_trial(**response)
            raise

        self.write_trial(**response)

    def show_instructions(self):
        gap = 80
        title_y = self.win.size[1]/2 - gap
        visual.TextStim(text=TITLE, alignVert='top',
                        pos=[0, title_y], height=30, bold=True,
                        **self.text_kwargs).draw()
        visual.TextStim(text=INSTRUCTIONS, alignVert='top', height=20,
                        pos=[0, title_y-gap],
                        **self.text_kwargs).draw()
        self.win.flip()
        event.waitKeys(keyList=['space'])

    def break_screen(self):
        visual.TextStim(BREAK, **self.text_kwargs).draw()
        self.win.flip()
        event.waitKeys(keyList=['space'])

    def get_or_create_sounds(self, *args):
        """Get sounds by name or create them if they don't exist."""
        return [self.sounds.setdefault(name, sound.Sound(name))
                for name in args]

    def play_and_wait(self, snd, text=''):
        duration = snd.getDuration()
        snd.play()
        self.icon.draw()
        self.icon_label.setText(text)
        self.icon_label.draw()
        self.win.flip()
        core.wait(duration)
        self.win.flip()

    def write_trial(self, **trial_data):
        data = self.session.copy()
        if not trial_data:
            # Write header for data file
            row = self.DATA_COLS
        else:
            data.update(trial_data)
            row = []
            for name in self.DATA_COLS:
                value = data.get(name, '')
                if not value:
                    logging.warning('Data for col {} not found'.format(name))
                elif name in ['sound_x', 'sound_y']:
                    value = SimilarityJudgments.get_message_id_from_path(value)
                row.append(value)

            for x in trial_data.keys():
                if x not in self.DATA_COLS:
                    logging.warning('Data for {} not saved'.format(x))
        self.data_file.write(','.join(map(str, row))+'\n')

    @staticmethod
    def get_message_id_from_path(sound_path):
        # e.g., 'path/to/sound/filename.wav' -> 'filename'
		# Also needs to be able to handle sound_path == numpy.int64
		try:
			message_id = Path(sound_path).stem
		except TypeError:
			message_id = Path(int(sound_path)).stem

		return message_id


class Trials(object):
    def __init__(self, seed=None, completed_csv=None):
        # Start with info for (gen i, gen i + 1) edges.
        edges = pandas.read_csv('linear_edges.csv')

        try:
            previous_data = pandas.read_csv(completed_csv)
            completed_edges = Trials.edges_to_sets(previous_data)
        except ValueError, IOError:
            logging.warning('Could not find existing data. Running all trials.')
            trials = edges  # all trials are new
        else:
            trials = Trials.remove_completed_trials(edges, completed_edges)

        self.random = numpy.random.RandomState(seed)
        trials.insert(0, 'block_ix',
                      self.random.choice(range(1,5), len(trials)))
        trials = (trials.sort_values('block_ix')
                        .reset_index(drop=True))
        trials.insert(0, 'trial_ix', range(1, len(trials)+1))

        trials['reversed'] = self.random.choice(range(2), len(trials))
        trials['category'] = Trials.determine_imitation_category(trials.sound_x)
        # Assumes that sound_x and sound_y come from the same category!

        self.trials = trials

    def blocks(self):
        blocks = [block.itertuples()
                  for _, block in self.trials.groupby('category')]
        self.random.shuffle(blocks)
        return blocks

    @staticmethod
    def remove_completed_trials(edges, completed_edges):
        is_unfinished = (pandas.Series(Trials.edges_to_sets(edges),
                                       index=edges.index)
                               .apply(lambda x: x not in completed_edges))
        unfinished = edges[is_unfinished]
        logging.warning('Dropped {} of {} total trials ({} left)'.format(
            (~is_unfinished).sum(), len(edges), len(unfinished)
        ))
        return unfinished

    @staticmethod
    def edges_to_sets(edges):
        stem = lambda x: SimilarityJudgments.get_message_id_from_path(x)
        return [{stem(edge.sound_x), stem(edge.sound_y)}
                for edge in edges.itertuples()]

    @staticmethod
    def determine_imitation_category(audio):
        messages = read_downloaded_messages()
        update_audio_filenames(messages)
        categories = messages[['audio', 'category']]
        categories.set_index('audio', inplace=True)
        return categories.reindex(audio).category.tolist()


class RatingScale(object):
    QUESTION = "Rate the similarity between the two sounds"
    NOTES = "To hear the sounds again, press 'r'. If there was an error, press 'e' to report it. To quit the experiment, press 'q'. You can resume it later."
    VALUES = range(1, 8)
    KEYBOARD = dict(q='quit', e='error', r='repeat')
    KEYBOARD.update({str(i): i for i in VALUES})
    X_GUTTER = 80
    LABEL_Y = 50
    FONT_SIZE = 30
    HIGHLIGHT_TIME = 0.5

    def __init__(self, text_kwargs):
        win = text_kwargs['win']
        self.flip = win.flip

        x_positions = numpy.array([(i-1) * self.X_GUTTER for i in self.VALUES])
        x_positions = x_positions - x_positions.mean()
        assert x_positions.max() < win.size[0]/2, "some ratings will be hidden"

        # Create text stim objects for all values of the scale
        self.ratings = [visual.TextStim(text=i, pos=(x, 0), height=30,
                                        **text_kwargs)
                        for i, x in zip(self.VALUES, x_positions)]

        # Label some of the scale points
        label_names = {1: 'Not at all', 7: 'Exact matches'}
        self.labels = [visual.TextStim(text=text,
                                       pos=(x_positions[x-1], -self.LABEL_Y),
                                       height=20, **text_kwargs)
                       for x, text in label_names.items()]

        # Create a title for the question
        self.title = visual.TextStim(text=self.QUESTION, height=30, bold=True,
                                     pos=(0, self.LABEL_Y), **text_kwargs)

        # Add note about other valid responses
        self.notes = visual.TextStim(text=self.NOTES, height=12,
                                     pos=(0, -2*self.LABEL_Y), **text_kwargs)

    def draw(self, flip=True):
        self.title.draw()
        for rating in self.ratings:
            rating.draw()
        for label in self.labels:
            label.draw()
        self.notes.draw()

        if flip:
            self.flip()

    def get_response(self):
        keyboard_responses = event.waitKeys(keyList=self.KEYBOARD.keys())
        key = self.KEYBOARD.get(keyboard_responses[0])
        if key == 'quit':
            raise QuitExperiment
        elif key == 'error':
            raise ReportError
        elif key == 'repeat':
            raise RepeatTrial
        self.highlight(key)
        return key

    def highlight(self, key):
        selected = self.ratings[int(key)-1]
        selected.setColor('green')
        self.draw()
        core.wait(self.HIGHLIGHT_TIME)
        selected.setColor('white')


class TextEntryForm(object):
    def __init__(self, text_kwargs, title=None, title_y=200, text_box_top=150):
        title = title or ERROR_FORM_TITLE
        self.text_box_title = visual.TextStim(text=title, pos=(0, title_y),
                                              bold=True, **text_kwargs)
        self.text_box = visual.TextStim(pos=(0, text_box_top), alignVert='top',
                                        **text_kwargs)
        self.flip = text_kwargs['win'].flip

    def get_response(self):
        self.text_box_title.draw()
        self.flip()

        response = ''
        typing = True
        while typing:
            for key in event.getKeys():
                if key in ['enter', 'return']:
                    typing = False
                    break
                elif key == 'backspace' and len(response) > 0:
                    response = response[:-1]
                elif key in string.lowercase + string.digits:
                    response += key
                elif key == 'space':
                    response += ' '

                self.text_box_title.draw()
                self.text_box.setText(response)
                self.text_box.draw()
                self.flip()

        return response


def get_player_info():
    info = {'Name': ''}
    dlg = gui.DlgFromDict(info, title='Similarity Judgments')
    if not dlg.OK:
        core.quit()
    clean = {key.lower(): value for key, value in info.items()}
    return clean


class QuitExperiment(Exception):
    pass

class ReportError(Exception):
    pass

class RepeatTrial(Exception):
    pass

if __name__ == '__main__':
    logging.console.setLevel(logging.WARNING)
    player = get_player_info()
    judgments = SimilarityJudgments(player, overwrite=False)
    judgments.run()
