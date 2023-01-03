# Web scraping
from importlib.resources import files
# from msilib.schema import ComboBox
import requests
import urllib

# Handling geojson files
import geopandas as gpd
import pandas as pd
import numpy as np
# Each building label is represented as a Point object
# From shapely
from shapely.geometry.point import Point
# Finds the country
import country_bounding_boxes as cbb
from rasterio.coords import BoundingBox

# Others
from typing import List, Optional
import zipfile
import sys
import os

from src.data_loading.utils import *
from src.data_loading.tif_links_utils import get_list_of_bounds_for_hurricane

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))


def get_vector_data_links(hurricane_name: str = DEFAULT_HURRICANE, toprint: bool = True) -> List:
    """
    Get a list of vector data links for the hurricane with hurricane_name
    The list must exist on github
    """
    filename = hurricane_name + FILE_LIST_SUFFIX
    file_list_path = FILE_LIST_PREFIX + filename
    response = requests.get(file_list_path)
    assert response.status_code == 200, f"Unsuccessful request! Status code: {response.status_code}"
    data = response.text
    assert data is not None, "No data!"
    L = data.split("\n")
    links = [link.strip() for link in L if ".zip" in link]
    print_message(toprint, f"There are in total {len(links)} links.")
    return links


def load_vector_data_link(vector_data_link, hurricane_name: str = DEFAULT_HURRICANE) -> str:
    """
    Given a link to the vector data, will download the (zip) file & extract it 
    Will save the file in the correct directory in /data
    """
    # Download and extract the zip file
    filename = vector_data_link.split("/")[-1]  # name of the zip file
    destination_dir = os.path.join(PATH_TO_DATA_RAW, f"{hurricane_name}-vector-data")

    if not os.path.isdir(destination_dir):
        os.mkdir(destination_dir)
    if not os.path.isfile(filename):
        urllib.request.urlretrieve(vector_data_link, filename=filename)

    with zipfile.ZipFile(filename, 'r') as zip_ref:
        zip_ref.extractall(destination_dir)

    # After extraction, delete the zip file
    os.remove(os.path.join(PATH_TO_DIR, filename))
    return destination_dir


def find_all_files_with_extension_in_dir(dirname: str, desired_extension: str, files: Optional[List] = None) -> List:
    """
    Given a directory, finds a list of paths to files with extension 
    
    EXAMPLE:
    --- 
    Using desired_extension = ".geojson", will return a list of paths to all
    geojson files in the directory 
    """
    if files is None:
        files = []
    for name in os.scandir(dirname):
        if os.path.isdir(name):
            files = find_all_files_with_extension_in_dir(name.path, desired_extension, files)
        else:
            if os.path.isfile(name):
                extension = os.path.splitext(name)[1]
                if extension == desired_extension:
                    files.append(name.path)
    return files


def load_all_vector_data_for_hurricane(hurricane_name: str = DEFAULT_HURRICANE, toprint: bool = True) -> List:
    """
    RETURNS
    ---
        files: a list of paths to all the geojson files related to hurricane_name
    """
    links = get_vector_data_links(hurricane_name, toprint)
    count = len(links)
    print_message(toprint, "Extracting files...")
    if count == 0:
        raise ValueError("No links available!")
    for (link, idx) in zip(links, list(range(count))):
        print_message(toprint, f"{idx + 1}/{count}")
        destination_dir = load_vector_data_link(link, hurricane_name)
    print_message(toprint, f"Extracted files can be found in {destination_dir}")
    geojson_files = find_all_files_with_extension_in_dir(destination_dir, ".geojson", [])
    print_message(toprint, f"There are {len(geojson_files)} geojson files available")
    return geojson_files


def combine_all_vector_data(hurricane_name: str, toprint: bool, overwrite: bool):
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
    print_message(toprint, f"Retrieving all vector data files for hurricane {hurricane_name}...")
    files = load_all_vector_data_for_hurricane(hurricane_name, toprint)
    assert len(files) > 0, f"No geojson data files available for hurricane {hurricane_name}!"
    path = files.pop()
    res = gpd.read_file(path)
    while len(files) > 0:
        path = files.pop()
        temp = gpd.read_file(path)
        res = pd.concat([res, temp])
    print_message(toprint, f"There are in total {len(res)} rows")
    res.to_file(path, driver="GeoJSON")
    print_message(toprint, f"Successfully saved vector data as a geojson file to:\n{path}")
    return res


def combine_all_vector_data_and_save_for_hurricane(hurricane_name: str = DEFAULT_HURRICANE, toprint: bool = True, overwrite: bool = False):
    # This is the path to the processed vector data file
    if not os.path.isdir(PATH_TO_GEOJSONS):
        os.mkdir(PATH_TO_GEOJSONS)
    path = os.path.join(PATH_TO_GEOJSONS, hurricane_name + ".geojson")
    # If there is already a processed data file
    if os.path.isfile(path) and not overwrite:
        return gpd.read_file(path)

    res = combine_all_vector_data(hurricane_name, toprint, overwrite=True)

    # We only keep the points
    # for which we have image data
    print_message(toprint, "Trimming...")
    trimmed = trim_gdf(gpd.GeoDataFrame(res), hurricane_name, toprint)
    print_message(toprint, f"There are {len(trimmed)} buildings in total after trimming")

    # We only want points that are buildings, not other things
    print_message(toprint, "Filtering...")
    trimmed_filtered = trimmed.loc[trimmed.label == "Flooded / Damaged Building"].copy()
    print_message(toprint, f"There are {len(trimmed_filtered)} buildings in total after filtering")

    # Add country names
    print_message(toprint, "Adding country names...")
    add_country_names(trimmed_filtered, hurricane_name, toprint)

    # Save processed vector data
    trimmed_filtered.to_file(path, driver="GeoJSON")
    print_message(toprint, f"Successfully saved trimmed vector data as a geojson file to:\n{path}")
    return trimmed_filtered


def check_point_in_bounding_box(point: Point, box: BoundingBox) -> bool:
    return (box.left < point.x < box.right) and (box.bottom < point.y < box.top)


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


def trim_gdf(gdf: gpd.GeoDataFrame, hurricane_name: str, toprint: bool):
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


def find_countries_for_point(point: Point) -> str:
    """
    Find the country that the point is in
    
    RETURNS:
    ---
        The country/countries that the point is in, separated by commas
    """
    cs = [c.name for c in cbb.country_subunits_containing_point(point.x, point.y)]
    return ", ".join(cs)


def add_country_names(gdf: gpd.GeoDataFrame, hurricane_name: str, toprint: bool) -> None:
    gdf["country"] = gdf.geometry.apply(
        lambda point: find_countries_for_point(point)
    )
    if toprint:
        countries = {}
        for p in gdf.geometry.tolist():
            cs = [c.name for c in cbb.country_subunits_containing_point(p.x, p.y)]
            for c in cs:
                if c not in countries.keys():
                    countries[c] = 1
                else:
                    countries[c] += 1
        print(f"The countries in the dataset for {hurricane_name} are: ")
        for c in countries.keys():
            print(c, " ", countries[c])
        print("---------------")
        print("Total: ", sum([countries[c] for c in countries.keys()]))


if __name__ == "__main__":
    df = combine_all_vector_data_and_save_for_hurricane("test", toprint=True, overwrite=True)
    print(df.info())
