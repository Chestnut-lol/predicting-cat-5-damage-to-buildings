# from email import contentmanager
import os
import sys
import affine
import numpy as np
import geopandas as gpd
import rasterio as rio

from typing import List

from rasterio.windows import from_bounds
from rasterio.io import MemoryFile
from rasterio.crs import CRS
from shapely.geometry.point import Point
from shapely.geometry import box

from src.data_loading.vector_data_utils import check_point_in_bounding_box, combine_all_vector_data_and_save_for_hurricane
from src.data_loading.tif_links_utils import get_tidied_tif_links
from src.data_loading.utils import convert_meters_to_deg, print_message, PATH_TO_PATCHES, DEFAULT_HURRICANE

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))


def get_indices_for_point(bounds_list: List, point: Point) -> List:
    """
    Parameters
    ----------
    bounds_list : a list of BoundingBox
    point : shapely.geometry.point.Point

    Returns
    -------
    res : a list of indices
        for each index i, bounds_list[i] is a bound that contains the point
    """
    res = []
    for idx, bound in enumerate(bounds_list):
        if check_point_in_bounding_box(point, bound):
            res.append(idx)
    return res


def get_geom_for_point(point: Point, dist: float):
    """
    Create a BoundingBox with the point at the center. 
    Each edge is at a distance of dist meters from the point.

    Parameters
    ----------
    point : shapely.geometry.point.Point
    dist : float

    Returns
    -------
    geodf : geopandas.geodataframe.GeoDataFrame
        geodataframe of the bounding box
    """
    deg = convert_meters_to_deg(dist)
    left, right, top, bottom = (point.x - deg, point.x + deg, point.y + deg, point.y - deg)
    geodf = gpd.GeoDataFrame(
        geometry=[
            box(left, bottom, right, top)
        ],
        crs="EPSG:4326"  # use lat lon crs system
    )
    return geodf


def create_dataset(data: np.ndarray, crs: CRS, count: int, transform: affine.Affine) -> rio.io.DatasetReader:
    # Receives a 2D array, a transform and a crs to create a rasterio dataset
    memfile = MemoryFile()
    dataset = memfile.open(driver='GTiff', height=data.shape[1], width=data.shape[2], count=count, crs=crs,
                           transform=transform, dtype=data.dtype)
    dataset.write(data)
    return dataset


def crop_patches_for_point(
        links: List,
        bounds_list: List,
        point: Point,
        point_idx: int,
        dist: float,
        path_to_dir: str,
        toprint: bool = True
    ):
    """
    PARAMETERS:
    ---
        links: a list of links
        bounds_list: a list of BoundingBox from rasterio.coords 
        point: the point that we want to crop patches for
        path_to_dir: path to the directory in which we will store all the patches
    """
    print_message(toprint, "Setting up...")
    geodf = get_geom_for_point(point, dist)
    (left, bottom, right, top) = geodf.geometry[0].bounds
    print_message(toprint, "Getting list of indices for point...")
    indices = get_indices_for_point(bounds_list, point)
    print_message(toprint, f"Cropping from a total of {len(indices)} images...")
    for idx, i in enumerate(indices):
        print_message(toprint, f"{idx + 1}/{len(indices)}", end="\r")
        link = links[idx]
        with rio.open(link) as src:
            window = from_bounds(
                left, bottom, right, top, src.transform,
            )
            window_transform = src.window_transform(window)
            clipped = src.read(window=window)
            crs = src.crs
            count = src.count
        print_message(toprint, f"Clipped data has shape: {clipped.shape}")
        print_message(toprint, "Saving...")
        filename = os.path.join(path_to_dir, f"{point_idx}-{i + 1}.tif")
        with rio.open(
                filename, 'w',
                driver='GTiff',
                width=clipped.shape[2],
                height=clipped.shape[1],
                count=count,
                transform=window_transform,
                crs=crs,
                dtype=clipped.dtype,
        ) as dst:
            dst.write(clipped)


def main(hurricane_name: str = DEFAULT_HURRICANE, toprint: bool = True) -> None:
    links = get_tidied_tif_links(hurricane_name, toprint)
    pre_event_links = [link for link in links if "pre-event" in link]
    post_event_links = [link for link in links if "post-event" in link]
    pre_event_bounds = [rio.open(link).bounds for link in pre_event_links]
    post_event_bounds = [rio.open(link).bounds for link in post_event_links]

    gdf = combine_all_vector_data_and_save_for_hurricane(hurricane_name, toprint)
    if len(gdf) == 0:
        raise Exception(f"No processed vector data for hurricane {hurricane_name}")

    path_to_hurricane_patches = os.path.join(PATH_TO_PATCHES, hurricane_name)
    path_to_hurricane_patches_pre = os.path.join(path_to_hurricane_patches, "pre")
    path_to_hurricane_patches_post = os.path.join(path_to_hurricane_patches, "post")
    os.makedirs(path_to_hurricane_patches, exist_ok=True)
    os.makedirs(path_to_hurricane_patches_pre, exist_ok=True)
    os.makedirs(path_to_hurricane_patches_post, exist_ok=True)

    for (point, idx) in zip(gdf.geometry, range(len(gdf))):
        crop_patches_for_point(pre_event_links, pre_event_bounds, point, idx, 20, path_to_hurricane_patches_pre,
                               toprint)
        crop_patches_for_point(post_event_links, post_event_bounds, point, idx, 20, path_to_hurricane_patches_post,
                               toprint)


if __name__ == "__main__":
    hurricane_name = input("Please input hurricane name (Press enter to use default test data):")
    hurricane_name = hurricane_name.strip()
    hurricane_name = hurricane_name.lower()
    main(hurricane_name)
