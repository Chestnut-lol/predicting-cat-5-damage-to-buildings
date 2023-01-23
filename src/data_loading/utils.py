import os
import math


PATH_TO_SRC = os.path.join(os.path.dirname(__file__), '..')
PATH_TO_DIR = os.path.join(PATH_TO_SRC, '..')
PATH_TO_DATA = os.path.join(PATH_TO_DIR, "data")
PATH_TO_DATA_RAW = os.path.join(PATH_TO_DATA, "raw")
PATH_TO_DATA_PROCESSED = os.path.join(PATH_TO_DATA, "processed")
PATH_TO_PATCHES = os.path.join(PATH_TO_DATA_PROCESSED, "patches")
PATH_TO_GEOJSONS = os.path.join(PATH_TO_DATA_PROCESSED, "geojsons")
PATH_TO_TIDIED_FILELISTS = os.path.join(PATH_TO_DATA_PROCESSED, "digital-globe-file-lists-tidied")

FILE_LIST_PREFIX = "https://raw.githubusercontent.com/Chestnut-lol/predicting-cat-5-damage-to-buildings/main/data/raw/digital-globe-file-lists/"
FILE_LIST_SUFFIX = "_file_list.txt"
DEFAULT_HURRICANE = "irma"

earth_radius = 6371 * 10**3


def print_message(toprint: bool, message: str, end="\n") -> None:
    if toprint:
        print(message)


def check_if_file_exist(path: str, delete_if_exist: bool) -> bool:
    if os.path.isfile(path):
        if delete_if_exist:
            os.remove(path)
            return False
        else:
            return True
    return False


def convert_meters_to_deg(meters: float) -> float:
    return (180 * meters) / (earth_radius * math.pi)


def convert_deg_to_meters(deg: float) -> float:
    return (earth_radius * math.pi * deg) / 180
