import argparse


parser = argparse.ArgumentParser(
    description="VessEval is a tool for the evaluation of pulmonary artery muscularization",
    formatter_class=argparse.ArgumentDefaultsHelpFormatter,
)
parser.add_argument(
    "-i", "--image", type=str, default="", help="open the image on startup"
)
parser.add_argument(
    "--segment_anything", action="store_true", help="start the GUI in segmentation mode"
)
args = parser.parse_args()

if args.segment_anything:
    from .sam.app import App

    app = App()
    app.mainloop()
else:
    from .views.app import App
    from .views.app.state import app_state

    app_state.filename_state.set(args.image)

    app = App()
    app.mainloop()
