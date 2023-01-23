# Handle tif files
# from asyncio.format_helpers import _format_callback_source
# from genericpath import isfile
import rasterio as rio
# import affine

# Some useful things from rasterio
from rasterio.coords import BoundingBox

# Web scraping
import requests

# Others
import sys
import os
from typing import List

from src.data_loading.utils import DEFAULT_HURRICANE, FILE_LIST_PREFIX, FILE_LIST_SUFFIX, PATH_TO_TIDIED_FILELISTS
from src.data_loading.utils import print_message

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))


def get_raw_tif_links(hurricane_name: str = DEFAULT_HURRICANE, toprint: bool = True) -> List:
    """
    Get a list of tif links for the hurricane with hurricane_name
    The list must exist on github

    Parameters
    ----------
    hurricane_name : str
        Name of the hurricane to get the raw tif links
    toprint : bool, optional
        bool to be passed to print_message helper function, see print_message(), default True

    Returns
    -------
    links : list
        list of the links of the tif files to download
    """
    filename = hurricane_name + FILE_LIST_SUFFIX
    file_list_path = FILE_LIST_PREFIX + filename
    response = requests.get(file_list_path)
    assert response.status_code == 200, f"Unsuccessful request! Status code: {response.status_code}" + \
                                        "\nThis may because you input an incorrect name for the hurricane"
    data = response.text
    assert data is not None, "No data!"
    L = data.split("\n")
    links = [link.strip() for link in L if ".tif" in link]
    print_message(toprint, f"There are in total {len(links)} links.")
    return links


def tidy_up_tif_links(links: List, hurricane_name: str, toprint: bool = True, overwrite: bool = False) -> List:
    """
    Given a list of tif links, will discard links that are useless, i.e. having less than 3 bands.
    Will then save the tidied list of links in ./data/processed/digital-globe-file-list-tidied
    
    Parameters
    ----------
    links : list
        list of links
    hurricane_name : str
        name of the hurricane to use
    toprint : bool, optional
        bool to be passed to print_message helper function, see print_message(), default True
    overwrite : bool, optional
        bool to overwrite hurricane_file_list_tidied if True, default False

    Returns
    -------
    res : list
        list of tidy up links
    """
    if len(links) == 0:
        raise ValueError("Empty list of links!")
    if not overwrite:
        # Check if tidied file exists and if so get_tided_tif_links
        # maybe redundant from the way this function is called
        if os.path.isdir(PATH_TO_TIDIED_FILELISTS):
            path = os.path.join(PATH_TO_TIDIED_FILELISTS, hurricane_name)
            if os.path.isfile(path):
                return get_tidied_tif_links(hurricane_name)
    if not os.path.isdir(PATH_TO_TIDIED_FILELISTS):
        os.mkdir(PATH_TO_TIDIED_FILELISTS)
    res = []
    before_count = len(links)
    print_message(toprint, f"Tidying up a total of {before_count} links...")
    # Only want tif files with band >= 3
    for idx, link in enumerate(links):
        print_message(toprint, f"{idx + 1}/{before_count}", end="\r")
        try:
            with rio.open(link) as src:
                if src.count >= 3:
                    res.append(link)
        except rio.errors.RasterioIOError:
            pass
    after_count = len(res)
    print_message(toprint, f"Before: {before_count} links \nAfter: {after_count} links")
    path = os.path.join(PATH_TO_TIDIED_FILELISTS, hurricane_name)

    with open(path, "w") as f:
        for link in res:
            f.write(link + "\n")
    return res


def get_tidied_tif_links(hurricane_name: str = DEFAULT_HURRICANE, toprint: bool = True) -> List:
    """
    Get a list of tidied tif links for the hurricane with hurricane_name
    If the tidied file list does not exist, will look for raw data & tidy up

    Parameters
    ----------
    hurricane_name : str
        name of the hurricane to use
    toprint : bool, optional
        bool to be passed to print_message helper function, see print_message(), default True

    Returns
    -------
    list
        list of links of the tifs
    """
    file_list_path = os.path.join(PATH_TO_TIDIED_FILELISTS, hurricane_name)
    if not os.path.isfile(file_list_path):
        links = get_raw_tif_links(hurricane_name, toprint)
        res = tidy_up_tif_links(links, hurricane_name, toprint)
        assert os.path.isfile(file_list_path) == True, "file should exist now!"
        return res
    else:
        data = open(file_list_path, "r")
        L = data.readlines()
        data.close()
        links = [link.strip() for link in L if ".tif" in link]
        return links


def find_useful_links_for_box(links: List, box: BoundingBox, toprint: bool = True) -> List:
    """
    Find useful tiff links that overlap with the bounding box

    Parameters
    ----------
    links : list
        list of the links to use
    box : rasterio.coords.BoundingBox
        boundingBox to use
    toprint : bool, optional
        bool to be passed to print_message helper function, see print_message(), default True

    Returns
    -------
    res : list
        list of the links that overlap with the box
    """
    before_count = len(links)
    res = []
    # for (link, idx) in zip(links, list(range(before_count))):
    for idx, link in enumerate(links):
        print_message(toprint, f"{idx + 1}/{before_count}")
        src = rio.open(link)
        if not rio.coords.disjoint_bounds(box, src.bounds):
            res.append(link)
    after_count = len(res)
    print_message(toprint, f"Before: {before_count} links \nAfter: {after_count} links")
    return res


def make_bounding_box_and_find_useful_links(
        left: float,
        bottom: float,
        right: float,
        top: float,
        links: List,
        toprint: bool = True
) -> tuple:
    """
    Parameters
    ----------
    left : float
    bottom : float
    right : float
    top : float
        coordinates for the bounding box
    links: list
        list of the links to use
    toprint : bool, optional
        bool to be passed to print_message helper function, see print_message(), default True

    Returns
    -------
    (boundingBox, useful-pre-event-links, useful-post-event-links)
    """
    box = BoundingBox(left, bottom, right, top)
    pre_event_links = [link for link in links if "pre-event" in link]
    post_event_links = [link for link in links if "post-event" in link]
    print_message(toprint, "Finding pre event links...")
    useful_pre_event_links = find_useful_links_for_box(pre_event_links, box, toprint)
    print_message(toprint, "Finding post event links...")
    useful_post_event_links = find_useful_links_for_box(post_event_links, box, toprint)
    print_message(toprint, f"Found {len(pre_event_links)} pre event links")
    print_message(toprint, f"Found {len(post_event_links)} post event links")
    return (box, useful_pre_event_links, useful_post_event_links)


def get_list_of_bounds_for_hurricane(hurricane_name: str = DEFAULT_HURRICANE, toprint: bool = True) -> dict:
    """
    Parameters
    ----------
    hurricane_name : str, optional
        name of the hurricane to use, default DEFAULT_HURRICANE i.e. irma
    toprint : bool, optional
        bool to be passed to print_message helper function, see print_message(), default True

    Returns
    -------
    res : dict
        dictionary of the links with the following structure:
            key is "pre" is the list of bounds of the sources obtained from pre_event_links
            key is "post" is the list of bounds of the sources obtained from post_event_links
    """
    res = dict()
    good_links = get_tidied_tif_links(hurricane_name, toprint)
    pre_event_links = [link for link in good_links if "pre-event" in link]
    post_event_links = [link for link in good_links if "post-event" in link]
    pre_event_bounds = [rio.open(link).bounds for link in pre_event_links]
    post_event_bounds = [rio.open(link).bounds for link in post_event_links]
    res["pre"] = pre_event_bounds
    res["post"] = post_event_bounds
    return res
