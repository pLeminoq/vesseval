from __future__ import annotations

from typing import Dict, List, Optional

import numpy as np
from numpy.typing import NDArray
from widget_state import ListState

from .point import PointState


class ContourState(ListState):

    def __init__(self, points: Optional[List[PointState]] = None) -> None:
        super().__init__(points if points is not None else [])

    @classmethod
    def from_numpy(cls, contour: NDArray[np.int64]) -> ContourState:
        contour = contour.astype(int).tolist()
        return cls([PointState(*pt) for pt in contour])

    def to_numpy(self) -> NDArray[np.int64]:
        return np.array([(pt.x.value, pt.y.value) for pt in self])

    def deserialize(self, points: List[Dict[str, int]]) -> None:
        with self:
            self.clear()

            for pt in points:
                self.append(PointState(**pt))
