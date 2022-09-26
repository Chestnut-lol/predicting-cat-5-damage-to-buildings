import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from data_loading.utils import *
from data_loading.tif_links_utils import *
from data_loading.vector_data_utils import *
import rioxarray as rxr
import shapely
from shapely.geometry.point import Point
from shapely.geometry import box
from typing import List

def get_indices_for_point(bounds_list: List, point: Point):
    """
    PARAMETERS:
    --- 
    bounds_list: a list of BoundingBox
    point: a Point object from shapely

    RETURNS:
    ---
    indices: a list of indices
        for each index i, bounds_list[i] is a bound that contains the point
    """
    res = []
    for (bound, idx) in zip(bounds_list, range(len(bounds_list))):
        if check_point_in_bounding_box(point, bound):
            res.append(idx)
    return res

def get_geom_for_point(point: Point, dist):
    """
    Create a BoundingBox with the point at the center. 
    Each edge is at a distance of dist meters from the point
    """
    deg = convert_meters_to_deg(dist)
    left, right, top, bottom = (point.x - deg, point.x+deg, point.y+deg, point.y-deg)
    geodf = gpd.GeoDataFrame(
        geometry=[
            box(left, bottom, right, top)
        ],
        crs="EPSG:4326"
    )
    return geodf

def crop_patches_for_point(xds_list: List, bounds_list: List, point: Point, dist, path_to_dir, toprint = True):
    """
    PARAMETERS:
    ---
        xds_list: a list of xarray dataArray objects
        bounds_list: a list of BoundingBox from rasterio.coords 
        point: the point that we want to crop patches for
        path_to_dir: path to the directory in which we will store all the patches
    """
    print_message(toprint, "Setting up...")
    geodf = get_geom_for_point(point, dist)
    print_message(toprint, "Getting list of indices for point...")
    indices = get_indices_for_point(bounds_list, point)
    print_message(toprint, f"Cropping from a total of {len(indices)} images...")
    for (idx, i) in zip(indices, range(len(indices))):
        print_message(toprint, f"{idx+1}/{len(indices)}",end="\r")
        clipped = xds_list[idx].rio.clip(geodf.geometry, geodf.crs)
        filename = os.path.join(path_to_dir, f"{i+1}.tif")
        clipped.rio.to_raster(filename, compress='LZMA', tiled=True, dtype="int32")


def main(hurricane_name = DEFAULT_HURRICANE, toprint = True):
    links = get_tidied_tif_links(hurricane_name, toprint)
    pre_event_links = [link for link in links if "pre-event" in link]
    post_event_links = [link for link in links if "post-event" in link]
    pre_event_srcs = [rio.open(link) for link in pre_event_links]
    post_event_srcs = [rio.open(link) for link in post_event_links]
    pre_event_bounds = [src.bounds for src in pre_event_srcs]
    post_event_bounds = [src.bounds for src in post_event_srcs]
    pre_event_xds = [rxr.open_rasterio(src) for src in pre_event_srcs]
    del(pre_event_srcs)
    post_event_xds = [rxr.open_rasterio(src) for src in post_event_srcs]
    del(post_event_srcs)

    gdf = combine_all_vector_data_and_save_for_hurricane(hurricane_name, toprint)
    if len(gdf) == 0:
        raise Exception(f"No processed vector data for hurricane {hurricane_name}")
    path_to_hurricane_patches = os.path.join(PATH_TO_PATCHES, hurricane_name)
    path_to_hurricane_patches_pre = os.path.join(path_to_hurricane_patches, "pre")
    path_to_hurricane_patches_post = os.path.join(path_to_hurricane_patches, "post")
    os.makedirs(path_to_hurricane_patches, exist_ok = True)
    os.makedirs(path_to_hurricane_patches_pre, exist_ok = True)
    os.makedirs(path_to_hurricane_patches_post, exist_ok = True)
    for (point,idx) in zip(gdf.geometry,range(len(gdf))):
        path_to_dir_pre = os.path.join(path_to_hurricane_patches_pre, str(idx))
        path_to_dir_post = os.path.join(path_to_hurricane_patches_post, str(idx))
        crop_patches_for_point(pre_event_xds, pre_event_bounds, point, 20, path_to_dir_pre, toprint)
        crop_patches_for_point(post_event_xds, post_event_bounds, point, 20, path_to_dir_post, toprint)

if __name__ == "__main__":
    main("test")