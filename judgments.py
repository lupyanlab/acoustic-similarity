from psychopy import visual, core, event, sound, logging

from tasks.data import get_linear_edges


class SimilarityJudgments(object):
    """Judge the similarity between two sounds.

    On each trial, two buttons are presented on the screen.
    Clicking on these buttons playes one of the sounds.
    A response scale is presented along the bottom of
    the screen. Players rate the two sounds on a 7-point
    scale.

    Pressing 'q' during a trial causes the experiment to quit.
    """
    KEYBOARD = dict(q='quit')
    KEYBOARD.update({str(i): i for i in range(1, 8)})
    BUTTON_SIZE = 0.5

    def __init__(self, player):
        self.player = player
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
                self.judge_similarity(edge.sound_x, edge.sound_y)
            except QuitExperiment:
                break
        core.quit()

    def judge_similarity(self, sound_x_name, sound_y_name):
        event.clearEvents()
        self.mouse.clickReset()
        logging.info('X: {}, Y: {}'.format(sound_x_name, sound_y_name))

        sound_x = sound.Sound(sound_x_name)
        sound_y = sound.Sound(sound_y_name)

        self.sound_x_button.draw()
        self.sound_y_button.draw()
        self.win.flip()

        while True:
            key_responses = event.getKeys(keyList=self.KEYBOARD.keys())
            mouse_responses = self.mouse.getPressed()

            if key_responses:
                key = self.KEYBOARD.get(key_responses[0])
                if key == 'quit':
                    logging.info('key press requested experiment quit')
                    raise QuitExperiment
                print key  # record response
                break

            if mouse_responses and mouse_responses[0] == 1:
                pos = self.mouse.getPos()
                if self.sound_x_button.contains(pos):
                    sound_x.play()
                elif self.sound_y_button.contains(pos):
                    sound_y.play()
                else:
                    logging.info('mouse press outside of buttons')

            core.wait(0.1)


def get_player_info():
    return dict(name='pierce')


def get_edges_to_judge():
    edges = get_linear_edges()
    unique_edges = edges[['sound_x', 'sound_y']].drop_duplicates()
    return unique_edges.iloc[:10].itertuples()


def calculate_button_positions():
    gutter = 0.5
    height = 0
    left = (-gutter, height)
    right = (gutter, height)
    return left, right


class QuitExperiment(Exception):
    pass


if __name__ == '__main__':
    logging.console.setLevel(logging.INFO)
    player = get_player_info()
    judgments = SimilarityJudgments(player)
    judgments.run()
