import argparse

from .views.app import App
from .views.app.state import app_state

parser = argparse.ArgumentParser()
parser.add_argument("-i", "--image", type=str, default="")
args = parser.parse_args()

app_state.filename_state.set(args.image)

app = App()
app.mainloop()
