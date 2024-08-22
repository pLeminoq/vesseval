import os

from PIL import ImageTk
from PIL import Image as ImagePIL

_dir = os.path.dirname(__file__)


class Icon:

    def __init__(self, filename: str):
        self.filename = filename
        self.image = ImagePIL.open(self.filename)

    def tk_image(self, width: int = None, height: int = None):
        if width is None and height is None:
            width, height = self.image.size

        if width is None:
            width = round(height * self.image.size[0] / self.image.size[1])

        if height is None:
            height = round(width * self.image.size[1] / self.image.size[0])

        return ImageTk.PhotoImage(
            self.image.resize((width, height), resample=ImagePIL.Resampling.BILINEAR)
        )


icons = {
    "arrow": Icon(os.path.join(_dir, "icons", "arrow_selector.png")),
    "rectangle": Icon(os.path.join(_dir, "icons", "rectangle.png")),
    "eraser": Icon(os.path.join(_dir, "icons", "eraser.png")),
}
