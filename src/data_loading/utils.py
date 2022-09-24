import sys
import os
PATH_TO_SRC = os.path.join(os.path.dirname(__file__), '..')
PATH_TO_DIR = os.path.join(PATH_TO_SRC, '..')
PATH_TO_DATA = os.path.join(PATH_TO_DIR, "data")
PATH_TO_DATA_RAW = os.path.join(PATH_TO_DATA, "raw")
PATH_TO_DATA_PROCESSED = os.path.join(PATH_TO_DATA, "processed")
PATH_TO_PATCHES = os.path.join(PATH_TO_DATA_PROCESSED, "patches")

FILE_LIST_PREFIX = "https://raw.githubusercontent.com/Chestnut-lol/predicting-cat-5-damage-to-buildings/main/data/raw/digital-globe-file-lists/" 
FILE_LIST_SUFFIX = "_file_list.txt" 
DEFAULT_HURRICANE = "irma"

def print_message(toprint: bool, message: str, end = "\n"):
    if toprint:
        print(message)