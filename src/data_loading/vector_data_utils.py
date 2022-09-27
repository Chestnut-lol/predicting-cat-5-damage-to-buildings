# Web scraping
from http.cookiejar import DefaultCookiePolicy
import requests
import urllib

# Handling geojson files
import geopandas as gpd
import pandas as pd
import numpy as np
import shapely
from shapely.geometry.point import Point

from rasterio.coords import BoundingBox

# Others
from typing import List
import zipfile
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from data_loading.utils import *
from data_loading.tif_links_utils import get_list_of_bounds_for_hurricane

def get_vector_data_links(hurricane_name = DEFAULT_HURRICANE, toprint = True) -> List:
    """
    Get a list of vector data links for the hurricane with hurricane_name
    The list must exist on github
    """
    filename = hurricane_name + FILE_LIST_SUFFIX
    file_list_path = FILE_LIST_PREFIX + filename
    response = requests.get(file_list_path)
    assert response.status_code == 200, f"Unsuccessful request! Status code: {response.status_code}"
    data = response.text 
    assert data != None, "No data!"
    L = data.split("\n")
    links = [link.strip() for link in L if ".zip" in link]
    print_message(toprint, f"There are in total {len(links)} links.")
    return links

def load_vector_data_link(vector_data_link, hurricane_name = DEFAULT_HURRICANE):
    """
    Given a link to the vector data, will download the (zip) file & extract it 
    Will save the file in the correct directory in /data
    """
    # Download and extract the zip file
    filename = vector_data_link.split("/")[-1] # name of the zip file
    destination_dir = os.path.join(PATH_TO_DATA_RAW, f"{hurricane_name}-vector-data")
    destination_path = os.path.join(destination_dir, filename[:-4]+"geojson")
    
    if not os.path.isdir(destination_dir):
        os.mkdir(destination_dir)
    if not os.path.isfile(filename):
        urllib.request.urlretrieve(vector_data_link, filename=filename)

    with zipfile.ZipFile(filename, 'r') as zip_ref:
        zip_ref.extractall(destination_path)

    # After extraction, delete the zip file
    os.remove(os.path.join(PATH_TO_DIR,filename))
    return destination_dir

def find_all_files_with_extension_in_dir(dirname, extension, files = []):
    """
    Given a directory, finds a list of paths to files with extension 
    
    EXAMPLE:
    --- 
    Using extension = ".geojson", will return a list of paths to all
    geojson files in the directory 
    """
    for name in os.scandir(dirname):
        if os.path.isdir(name):
            files = find_all_files_with_extension_in_dir(name.path, extension, files)
        else:
            if os.path.isfile(name):
                extension = os.path.splitext(name)[1]
                if extension==".geojson":
                    files.append(name.path)
    return files

def load_all_vector_data_for_hurricane(hurricane_name = DEFAULT_HURRICANE, toprint = True) -> List:
    """
    RETURNS
    ---
        geojson_files: a list of paths to all the geojson files related to hurricane_name
    """
    links = get_vector_data_links(hurricane_name, toprint)
    count = len(links)
    print_message(toprint, "Extracting files...")
    if count == 0:
        raise ValueError("No links available!")
    for (link, idx) in zip(links, list(range(count))):
        print_message(toprint, f"{idx+1}/{count}")
        destination_dir = load_vector_data_link(link, hurricane_name)
    print_message(toprint, f"Extracted files can be found in {destination_dir}")
    geojson_files = find_all_files_with_extension_in_dir(destination_dir, ".geojson")
    print_message(toprint, f"There are {len(geojson_files)} geojson files available")
    return geojson_files

def combine_all_vector_data_and_save_for_hurricane(hurricane_name = DEFAULT_HURRICANE, toprint = True, overwrite = False):
    """
    Combines all geojson files for the hurricane into one geojson file
    The combined file will be saved in data/processed/geojson

    PARAMETERS:
    ---
        hurricane_name: name of the hurricane
        toprint: whether or not to print progress
        overwrite: whether or not to overwrite existing processed vector data
    """
    # This is the path to the processed vector data file
    if not os.path.isdir(PATH_TO_GEOJSONS):
        os.mkdir(PATH_TO_GEOJSONS)
    path = os.path.join(PATH_TO_GEOJSONS, hurricane_name + ".geojson")
    # If there is already a processed data file
    if os.path.isfile(path) and not overwrite: 
        return gpd.read_file(path)

    print_message(toprint, f"Retrieving all geojson files for hurricane {hurricane_name}...")
    geojson_files = load_all_vector_data_for_hurricane(hurricane_name, toprint)
    assert len(geojson_files) > 0, f"No geojson files available for hurricane {hurricane_name}!"
    path = geojson_files.pop()
    res = gpd.read_file(path)
    print_message(toprint, f"Current gpd has size {len(res)}")
    while len(geojson_files) > 0:
        path = geojson_files.pop()
        temp = gpd.read_file(path)
        res = pd.concat([res, temp])
        print_message(toprint, f"Current gpd has size {len(res)}")

    # We only keep the points
    # for which we have image data
    print_message(toprint, f"There are {len(res)} buildings in total before trimming")
    print_message(toprint, "Trimming...")
    trimmed_res = trim_gdf(gpd.GeoDataFrame(res), hurricane_name, toprint)
    print_message(toprint, f"There are {len(trimmed_res)} buildings in total after trimming")
    
    # Save processed vector data
    trimmed_res.to_file(path, driver="GeoJSON")
    print_message(toprint, f"Successfully saved trimmed vector data as a geojson file to:\n{path}")
    return trimmed_res

def check_point_in_bounding_box(point: Point, box: BoundingBox):
    return (box.left < point.x < box.right) and  (box.bottom < point.y < box.top)

def exist_link_containing_point(point: Point, bounds_list: List) -> bool:
    """
    PARAMETERS
    ---
        point: a Point object from shapely.geometry.point
        bounds_list: a list of BoundingBox objects
    """
    for bound in bounds_list:
        if check_point_in_bounding_box(point, bound):
            return True
    return False

def trim_gdf(gdf: gpd.GeoDataFrame, hurricane_name, toprint):
    """
    This trims down the geodataframe 
    and adds two extra cols: 
        exist_pre_event_imagery
        exist_post_event_imagery
    We only keep the points that we have image for
    """
    print_message(toprint, "Getting list of bounds...")
    bounds_dict = get_list_of_bounds_for_hurricane(hurricane_name, toprint)
    pre_image_cnt = len(bounds_dict["pre"])
    post_image_cnt = len(bounds_dict["post"])
    print_message(toprint, f"There are {pre_image_cnt} links of pre-images")
    print_message(toprint, f"There are {post_image_cnt} links of post-images")
    gdf["exist_post_event_imagery"] = gdf.geometry.apply(
        lambda point: exist_link_containing_point(
            point=point,
            bounds_list=bounds_dict["post"]
        )
    )
    print_message(toprint, f"There are {len(gdf.loc[gdf.exist_post_event_imagery])} buildings with post-event imagery")
    
    gdf["exist_pre_event_imagery"] = gdf.geometry.apply(
        lambda point: exist_link_containing_point(
            point=point,
            bounds_list=bounds_dict["pre"]
        )
    )
    print_message(toprint, f"There are {len(gdf.loc[gdf.exist_pre_event_imagery])} buildings with pre-event imagery")
    
    return gdf.loc[
        np.logical_or(
            gdf.exist_pre_event_imagery.to_numpy(),
            gdf.exist_post_event_imagery.to_numpy(),
        )
    ]

if __name__ == "__main__":
    combine_all_vector_data_and_save_for_hurricane()