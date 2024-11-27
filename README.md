# VessEval
Vess(el) eval(uation) is a small GUI application to evalute the muscularization of pulmonary vessels.

## Installation
* `pip install -r requirement.txt`

### Notes
Notes for my colleagues using Windows in a restrictive environment:
* Install [Git](https://git-scm.com/downloads)
* Configure git: `git config --global http.sslBackend schannel`
* Install [Python](https://www.python.org/downloads/)
* Install requirements: `pip install -r requirements.txt  --verbose --trusted-host pypi.python.org --trusted-host pypi.org --trusted-host files.pythonhosted.org`

## Run
* `python -m vesseval`

# Usage
[vesseval_demo.webm](https://github.com/user-attachments/assets/66f47dec-8b23-4105-b8e8-71e2dbc7eaf2)

To evaluate the muscularization of a pulmonary vessel, a rough outline must first be drawn.
In VessEval this is done by creating a bounding box.
The bounding box can then be refined:
* The vertices can be moved.
* Additional vertices can be added by double-clicking anywhere on the outline.
* Vertices can be removed by right-clicking.
You can also erase parts of an image.
This can be useful to eliminate things inside a vessel that prevent automatic evaluation.

Afterwards, you can either select _Process Contour_ from the _Tools_ menu or press the _Enter_ key.
This opens a window that allows preprocessing of the selected image regions.
Thresholds can be modified and open/close operations can be enabled and configured.

After clicking _Process_, VessEval will evaluate the vessel.
This step will detect and draw an inner contour (blue) and an outer contour (red) for the pulmonary cells (green) and the muscle cells (red), respectively.
These contours can be modified similar to the bounding box that outlines the vessel (see above).
The evaluated parameters can be copied to a single row of an Excel spreadsheet.





