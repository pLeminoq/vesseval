from typing import Any
from widget_state import HigherOrderState, IntState, State

from .point import PointState


class BoundingBoxState(HigherOrderState):

    def __init__(self, x1: int | IntState, y1: int, x2: int, y2: int):
        super().__init__()

        self.x1 = IntState(x1) if isinstance(x1, int) else x1
        self.y1 = IntState(y1) if isinstance(y1, int) else y1
        self.x2 = IntState(x2) if isinstance(x2, int) else x2
        self.y2 = IntState(y2) if isinstance(y2, int) else y2

    def tlbr(self) -> tuple[int, int, int, int]:
        return (self.x1.value, self.y1.value, self.x2.value, self.y2.value)

    def set(self, x1: int, y1: int, x2: int, y2: int):
        with self:
            self.x1.set(x1)
            self.y1.set(y1)
            self.x2.set(x2)
            self.y2.set(y2)

    def top_left(self):
        return PointState(self.x1, self.y1)

    def top_right(self):
        return PointState(self.x2, self.y1)

    def bottom_left(self):
        return PointState(self.x1, self.y2)

    def bottom_right(self):
        return PointState(self.x2, self.y2)

