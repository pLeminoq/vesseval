from typing import List

import numpy as np

from .lib import ListState
from .point import PointState

class ContourState(ListState):

    def __init__(self, points: List[PointState] = None):
        super().__init__(points if points is not None else [])

    @classmethod
    def from_numpy(cls, contour: np.ndarray):
        return cls([PointState(*pt) for pt in contour])

    def to_numpy(self):
        return np.array([(pt.x.value, pt.y.value) for pt in self])
