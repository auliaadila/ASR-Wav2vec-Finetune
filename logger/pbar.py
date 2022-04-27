from array import array
from tensorflow.keras.utils import Progbar

class PBar:
    def __init__(self, n_steps, width):
        self.n_steps = n_steps
        self.width = width
        self.pbar =  Progbar(self.n_steps, self.width)


    def update(self, step, mode, scores:dict):
        scores = [(mode + k, v) for k, v in scores.items()]
        self.pbar.update(step, scores)




    