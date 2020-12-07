import sys

sys.path.append('./water_observe/src')
import matplotlib.pyplot as plt

# mpl.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
from datetime import datetime
from shapely.geometry import shape
from shapely.wkt import loads
import urllib.request as request
import json
# from visualisation import plot_water_body
from geom_utils import get_bbox, get_optimal_resolution
from sh_requests import get_optical_data, get_S2_request, get_S2_wmsrequest
from s2_water_extraction import extract_surface_water_area_per_frame, surface_water_area_with_dem_veto
from sentinelhub import MimeType, CRS, BBox, SentinelHubRequest, SentinelHubDownloadClient, \
    DataCollection, bbox_to_dimensions, DownloadRequest
import geopandas as gpd
import datetime as dt
from sentinelhub import SHConfig
from sentinelhub import WmsRequest, WcsRequest, MimeType, CRS, BBox, DataCollection

config = SHConfig()
config.instance_id = 'ebb43985-6aca-476b-9719-fce4e7a54d60'

# get area
betsiboka_coords_wgs84 = [28.828, 41.179, 28.913, 41.221]  # lon1,lat1,lon2,lat2
resolution = 5
betsiboka_bbox = BBox(bbox=betsiboka_coords_wgs84, crs=CRS.WGS84)
betsiboka_size = bbox_to_dimensions(betsiboka_bbox, resolution=resolution)
resx, resy = get_optimal_resolution(betsiboka_bbox)

# get water polygon
file = '/home/cak/Desktop/lake_extraction/water_observe/data/data.geojson'
# water_polygon = gpd.read_file(file)

with open(file) as f:
    data = json.load(f)

nominal_outline = shape(data['features'][0]['geometry'])

# date = datetime(2020, 6, 20)
# the_dam_bbox = get_bbox(nominal_outline)
# resx, resy = get_optimal_resolution(the_dam_bbox)
#
# time_interval = ['2017-05-31', '2017-05-31']
#
# wb_url = 'https://water.blue-dot-observatory.com/api/waterbodies/38419/index.html'
# with request.urlopen(wb_url) as url:
#     wb_data = json.loads(url.read().decode())

# nominal_outline = shape(wb_data['nominal_outline']['geometry'])
date = datetime(2020, 6, 20)
the_dam_bbox = get_bbox(nominal_outline)
resx, resy = get_optimal_resolution(the_dam_bbox)
resx, resy = 30, 30

measurement = extract_surface_water_area_per_frame(42, nominal_outline, the_dam_bbox, date, resx, resy, config)

detected_water = loads(measurement.GEOMETRY)

# plot_water_body(get_optical_data(get_S2_request('TRUE-COLOR-S2-L1C', betsiboka_bbox, date, resx, resy, 0.2)),
#                 date, nominal_outline, betsiboka_bbox, detected_water, measurement.SURF_WATER_LEVEL)
