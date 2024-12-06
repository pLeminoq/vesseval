from typing import Optional
import threading

import cv2 as cv
import numpy as np
from PIL import ImageTk
from PIL import Image as PILImage
import tkinter as tk

from ...state import DisplayImageState
from ..util import stateful
from .lib import CanvasItem


def img_to_tk(img: np.ndarray) -> ImageTk:
    return ImageTk.PhotoImage(PILImage.fromarray(img))

@stateful
class Image(CanvasItem):

    def __init__(self, canvas: tk.Canvas, state: DisplayImageState):
        super().__init__(canvas, state)

        self.img_tk = None
        self.img_id = None

    def draw(self):
        self.canvas.event_generate
        if self.img_id is not None:
            self.canvas.delete(self.img_id)

        width, height = self.state.resolution_state.values()
        self.canvas.config(width=width, height=height)
        self.img_tk = img_to_tk(self.state.display_image_state.value)
        self.img_id = self.canvas.create_image(
            width // 2,
            height // 2,
            image=self.img_tk,
        )
        self.canvas.tag_lower(self.img_id)
