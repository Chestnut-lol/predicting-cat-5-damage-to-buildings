# Predicting Category 5 Hurricane Damage to Buildings

 [![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
 <a href="https://github.com/psf/black"><img alt="Code style: black" src="https://img.shields.io/badge/code%20style-black-000000.svg"></a>

## Requirements
- Python 3.9+

## Getting started
The main source codes are in the src/data_loading, with scripts to download data from DigitalGlobe. 

Setup:
1. Create a virtual environment
2. Install the packages in `requirements/requirements.txt`. There are a few packages that need to be installed manually, and the instructions can be found `requirements/README`

Workflow:
1. Go to DigitalGlobe https://www.maxar.com/open-data
2. Select an event of interest, for example hurricane irma: https://www.maxar.com/open-data/hurricane-irma
3. Select "File List" at the bottom of the page. Copy and paste the file to data/raw/digital-globe-file-list in the format of "{hurricane-name}_file_list.txt" (There are already two such file lists available, which are `irma_file_list.txt`,  `test_file_list.txt`)
4. For start, run the following commands in the terminal: `python .\src\data_loading\patch_utils.py`. There should be a prompt asking you to input a name for the hurricane. Press Enter straight away and the program should use the default testing data (which is smaller in size). 

The testing links can be found in data\processed\digital-globe-file-lists-tidied

## Project Organization
```
├── LICENSE
├── Makefile           <- Makefile with commands like `make init` or `make lint-requirements`
├── README.md          <- The top-level README for developers using this project.
|
├── notebooks          <- Jupyter notebooks. Naming convention is a number (for ordering),
|   |                     the creator's initials, and a short `-` delimited description, e.g.
|   |                     `1.0_jqp_initial-data-exploration`.
│   ├── exploratory    <- Notebooks for initial exploration.
│   └── reports        <- Polished notebooks for presentations or intermediate results.
│
├── report             <- Generated analysis as HTML, PDF, LaTeX, etc.
│   ├── figures        <- Generated graphics and figures to be used in reporting
│   └── sections       <- LaTeX sections. The report folder can be linked to your overleaf
|                         report with github submodules.
│
├── requirements       <- Directory containing the requirement files.
│
├── setup.py           <- makes project pip installable (pip install -e .) so src can be imported
├── src                <- Source code for use in this project.
│   ├── __init__.py    <- Makes src a Python module
│   │
│   ├── data_loading   <- Scripts to download or generate data
│   │
│   ├── preprocessing  <- Scripts to turn raw data into clean data and features for modeling
|   |
│   ├── models         <- Scripts to train models and then use trained models to make
│   │                     predictions
│   │
│   └── tests          <- Scripts for unit tests of your functions
│
└── setup.cfg          <- setup configuration file for linting rules
```

## Code formatting
To automatically format your code, make sure you have `black` installed (`pip install black`) and call
```black . ``` 
from within the project directory.

---

Project template created by the [Cambridge AI4ER Cookiecutter](https://github.com/ai4er-cdt/ai4er-cookiecutter).