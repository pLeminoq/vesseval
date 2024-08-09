import argparse

from .state import app_state
from .views.app import App

parser = argparse.ArgumentParser()
parser.add_argument("-i", "--image", type=str, default="")
args = parser.parse_args()

app_state.filename_state.set(args.image)

app = App()
app.mainloop()
