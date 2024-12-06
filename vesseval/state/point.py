from typing import Union

from widget_state import IntState, DictState


class PointState(DictState):
    """
    Point state that represents 2D pixel coordinates.

    It is often used for drawing.
    """

    def __init__(self, x: int | IntState, y: int | IntState):
        super().__init__()

        self.x = IntState(x) if isinstance(x, int) else x
        self.y = IntState(y) if isinstance(y, int) else y

if __name__ == "__main__":
    pt = PointState(5, 10)
    print(pt)
