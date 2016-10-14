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

    def __init__(self, player):
        self.player = player
        self.win = visual.Window()
        self.edges = get_edges_to_judge()
        self.mouse = event.Mouse(win=self.win)

    def run(self):
        for (sound_x, sound_y) in self.edges:
            try:
                self.judge_similarity(sound_x, sound_y)
            except QuitExperiment:
                break

    def judge_similarity(sound_x, sound_y):
        event.clearEvents()
        self.mouse.clickReset()

        while True:
            key_responses = event.getKeys(keyList=self.KEYBOARD.keys())
            mouse_responses = self.mouse.getPressed()

            if key_responses:
                key = self.KEYBOARD.get(key_response[0])
                if self.KEYBOARD.get(key) == 'quit':
                    logging.info('key press requested experiment quit')
                    raise QuitExperiment
                print key  # record response
                break

            if mouse_responses:
                pos = self.mouse.getPos()
                if self.sound_x_button.contains(pos):
                    sound_x.play()
                elif self.sound_y_button.contains(pos):
                    sound_y.play()
                else:
                    logging.info('mouse press outside of buttons')


def get_player_info():
    return dict(name='pierce')


def get_edges_to_judge():
    edges = get_linear_edges()
    unique_edges = edges[['sound_x', 'sound_y']].drop_duplicates()
    return unique_edges


if __name__ == '__main__':
    logging.console.setLevel(logging.INFO)
    player = get_player_info()
    judgments = SimilarityJudgments(player)
    judgments.run()
