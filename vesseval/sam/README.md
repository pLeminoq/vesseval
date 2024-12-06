# VessEval with SAM2

## Installation
* If not yet cloned `git clone https://github.com/pleminoq/vesseval`, otherwise update via `git pull`
* Install dependencies: `pip install -r requirements.txt  --verbose --trusted-host pypi.python.org --trusted-host pypi.org --trusted-host files.pythonhosted.org`
* Download the [SAM2 tiny model](https://dl.fbaipublicfiles.com/segment_anything_2/092824/sam2.1_hiera_tiny.pt) and copy it to `<vesseval_dir>/checkpoints/sam2.1_hiera_tiny.pt`

Note: VessEval attempts to download the SAM2 tiny model on startup. But this fails in the HDZ environment.

## Usage
* Start via `python -m vesseval --segment_anything` 
* Open an image via the file menu
* Segment regions with the SAM model:
  * A double-left-click will create a new region
  * By selecting the rectangle mode from the toolbar, you can create draw a rectangle with you mouse (hold left button)
  * A double-right-click will create a background point
* Select _Eval_ from the _Tools_ menu to evaluate region statistics
* Statistics are printed to console and are copied to clipboard. This means that you can paste the statistics to Excel. The types of the copied values are as follows: _index_, _area_, _perimeter_, _cut_off_, _roundndess_, _circularity_, _feret_max_, _feret_min_, _feret_perp_min_, _feret_max_angle_, _feret_min_angle_, _filename_ 

