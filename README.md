# VessEval
Vess(el) eval(uation) is a small GUI application to evaluate the muscularization of pulmonary vessels.

## System Requirements
#### Hardware
VessEval should run on any normal desktop computer.

#### Software
VessEval requires Python 3.10 or newer.
It was tested on Linux (Ubuntu 22.04) and Windows (10 & 11).

##### Dependencies
See [requirements.txt](requirements.txt).
Vesseval mainly depends on the image processing libraries OpenCV and Pillow.

## Installation
Currently VessEval can only be installed from Github:
```
git clone https://github.com/pleminoq/vesseval
pip install -r requirement.txt`
```

### Notes
Notes for my colleagues using Windows in a restrictive environment:
* Install [Git](https://git-scm.com/downloads)
* Configure git: `git config --global http.sslBackend schannel`
* Install [Python](https://www.python.org/downloads/)
* Install requirements: `pip install -r requirements.txt  --verbose --trusted-host pypi.python.org --trusted-host pypi.org --trusted-host files.pythonhosted.org`

## Run
* `python -m vesseval`

## Usage

#### Demo

[vesseval_demo.webm](https://github.com/user-attachments/assets/66f47dec-8b23-4105-b8e8-71e2dbc7eaf2)

The image seen in the demo is provided with VessEval.
It can be opened from [demo_data/example_image.tif](demo_data/example_image.tif).

#### Description
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

## How automatic Vessel processing works
After a vessel has been roughly outlined, this part of the image is cut out.
After this part of the image has maunally been preprocessed (thresholding, opening, closing), Vesseval `shoots` rays from its center in angle steps of 6°.
Each ray is checked for intersections with green pixels (vascular cells) or red pixels (muscle cells).
The innermost and outermost intersections with all rays form an inner and and outer contour and allow the calculation of vessel statistics.
