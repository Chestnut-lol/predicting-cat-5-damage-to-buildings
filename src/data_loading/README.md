# What are the .py files for?
- `__init__.py` makes `data_loading` into a python package, just ignore it
- `patch_utils.py` contain functions that work with patches. It is the main file to run for start 
- `tif_links_utils.py` are for downloading images using the tif links that we have in `data\raw\digital-globe-file-list`
- `utils.py` are for random useful functions
- `vector_data_utils.py` work with vector data (i.e. geojson files). Note that on the DigitalGlobe website the vector data all comes in different formats. Note that so far it does not have any capacity to work with shapefiles. If there are runtime errors, this file is likely to be the first to be blamed :(