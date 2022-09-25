# Handle tif files
import rasterio as rio
import rioxarray as rxr
import affine

# Some useful thiings from rasterio
from rasterio.coords import BoundingBox

# Handle geojson files
import geopandas as gpd

# Web scraping
import requests

# Others
from typing import List
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from data_loading.utils import *

def get_tif_links(hurricane_name = DEFAULT_HURRICANE, toprint = True) -> List:
    """
    Get a list of tif links for the hurricane with hurricane_name
    The list must exist on github
    """
    filename = hurricane_name + FILE_LIST_SUFFIX
    file_list_path = FILE_LIST_PREFIX + filename
    response = requests.get(file_list_path)
    assert response.status_code == 200, f"Unsuccessful request! Status code: {response.status_code}"
    data = response.text 
    assert data != None, "No data!"
    L = data.split("\n")
    links = [link.strip() for link in L if ".tif" in link]
    print_message(toprint, f"There are in total {len(links)} links.")
    return links

def tidy_up_tif_links(links: List, toprint = True) -> List:
    """
    Given a list of tif links, will discard links that are useless
    """
    if len(links) == 0:
        raise ValueError("Empty list of links!")
    res = [] 
    before_count = len(links)
    print_message(toprint, f"Tidying up a total of links {before_count} links...")
    # Only want tif files with band >= 3
    for (link,idx) in zip(links, list(range(before_count))):
        print_message(toprint, f"{idx+1}/{before_count}", end="\r")
        try:
            src = rio.open(link)
            if src.count >= 3:
                res.append(link)
        except:
            pass 
    after_count = len(res)
    print_message(toprint, f"Before: {before_count} links \nAfter: {after_count} links")
    return res

def find_useful_links_for_box(links: List, box: BoundingBox, toprint = True) -> List:
    """
    Find useful tiff links that overlap with the bounding box
    """
    before_count = len(links)
    res = []
    for (link, idx) in zip(links, list(range(before_count))):
        print_message(toprint, f"{idx+1}/{before_count}")
        src = rio.open(link)
        if not rio.coords.disjoint_bounds(box, src.bounds):
            res.append(link)
    after_count = len(res)
    print_message(toprint, f"Before: {before_count} links \nAfter: {after_count} links")
    return res

def make_bounding_box_and_find_useful_links(left, bottom, right, top, links, toprint = True) -> tuple:
    """
    PARAMETERS:
    ---
        left, bottom, right top: for making the bounding box
        links: list of links
    
    RETURNS:
    ---
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

def get_list_of_bounds_for_hurricane(hurricane_name = DEFAULT_HURRICANE, toprint = True) -> dict:
    """
    RETURNS:
    ---
        A dictionary, res, with keys: pre, post
        res["pre"]: list of bounds of the sources obtained from pre_event_links
        res["post"]: list of bounds of the sources obtained from post_event_links
    """
    res = dict()
    all_links = get_tif_links(hurricane_name, toprint)
    good_links = tidy_up_tif_links(all_links, toprint)
    pre_event_links = [link for link in good_links if "pre-event" in link]
    post_event_links = [link for link in good_links if "post-event" in link]
    pre_event_bounds = [rio.open(link).bounds for link in pre_event_links]
    post_event_bounds = [rio.open(link).bounds for link in post_event_links]
    res["pre"] = pre_event_bounds
    res["post"] = post_event_bounds
    return res