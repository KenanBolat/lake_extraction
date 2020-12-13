import sys

sys.path.append('./water_observe_old/src')
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
file = '/home/cak/Desktop/lake_extraction/water_observe_old/data/data.geojson'
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


import datetime

import matplotlib.pyplot as plt
import numpy as np

from sentinelhub import WmsRequest, BBox, CRS, MimeType, CustomUrlParam, get_area_dates
from s2cloudless import S2PixelCloudDetector, CloudMaskRequest


def overlay_cloud_mask(image, mask=None, factor=1. / 255, figsize=(15, 15), fig=None):
    """
    Utility function for plotting RGB images with binary mask overlayed.
    """
    if fig == None:
        plt.figure(figsize=figsize)
    rgb = np.array(image)
    plt.imshow(rgb * factor)
    if mask is not None:
        cloud_image = np.zeros((mask.shape[0], mask.shape[1], 4), dtype=np.uint8)
        cloud_image[mask == 1] = np.asarray([255, 255, 0, 100], dtype=np.uint8)
        plt.imshow(cloud_image)


def plot_probability_map(rgb_image, prob_map, factor=1. / 255, figsize=(15, 30)):
    """
    Utility function for plotting a RGB image and its cloud probability map next to each other.
    """
    plt.figure(figsize=figsize)
    plot = plt.subplot(1, 2, 1)
    plt.imshow(rgb_image * factor)
    plot = plt.subplot(1, 2, 2)
    plot.imshow(prob_map, cmap=plt.cm.inferno)


def plot_cloud_mask(mask, figsize=(15, 15), fig=None):
    """
    Utility function for plotting a binary cloud mask.
    """
    if fig == None:
        plt.figure(figsize=figsize)
    plt.imshow(mask, cmap=plt.cm.gray)


def plot_previews(data, dates, cols=4, figsize=(15, 15)):
    """
    Utility to plot small "true color" previews.
    """
    width = data[-1].shape[1]
    height = data[-1].shape[0]

    rows = data.shape[0] // cols + (1 if data.shape[0] % cols else 0)
    fig, axs = plt.subplots(nrows=rows, ncols=cols, figsize=figsize)
    for index, ax in enumerate(axs.flatten()):
        if index < data.shape[0]:
            caption = '{}: {}'.format(index, dates[index].strftime('%Y-%m-%d'))
            ax.set_axis_off()
            ax.imshow(data[index] / 255., vmin=0.0, vmax=1.0)
            ax.text(0, -2, caption, fontsize=12, color='g')
        else:
            ax.set_axis_off()


LAYER_NAME = 'TRUE-COLOR-S2-L1C'  # e.g. TRUE-COLOR-S2-L1C
bbox_coords_wgs84 = [-90.9216499, 14.4190528, -90.8186531, 14.5520163]
bounding_box = BBox(bbox_coords_wgs84, crs=CRS.WGS84)
INSTANCE_ID = 'ebb43985-6aca-476b-9719-fce4e7a54d60'
wms_true_color_request = WmsRequest(layer=LAYER_NAME,
                                    bbox=bounding_box,
                                    time=('2017-12-01', '2017-12-31'),
                                    width=600, height=None,
                                    image_format=MimeType.PNG,
                                    instance_id=INSTANCE_ID)
wms_true_color_imgs = wms_true_color_request.get_data()

bands_script = 'return [B01,B02,B04,B05,B08,B8A,B09,B10,B11,B12]'

wms_bands_request = WmsRequest(layer=LAYER_NAME,
                               custom_url_params={
                                   CustomUrlParam.EVALSCRIPT: bands_script,
                                   CustomUrlParam.ATMFILTER: 'NONE'
                               },
                               bbox=bounding_box,
                               time=('2017-12-01', '2017-12-31'),
                               width=600, height=None,
                               image_format=MimeType.TIFF_d32f,
                               instance_id=INSTANCE_ID)
wms_bands = wms_bands_request.get_data()

cloud_detector = S2PixelCloudDetector(threshold=0.4, average_over=4, dilation_size=2)
cloud_probs = cloud_detector.get_cloud_probability_maps(np.array(wms_bands))
cloud_masks = cloud_detector.get_cloud_masks(np.array(wms_bands))
image_idx = 0
overlay_cloud_mask(wms_true_color_imgs[image_idx], cloud_masks[image_idx])
plot_probability_map(wms_true_color_imgs[image_idx], cloud_probs[image_idx])
plot_cloud_mask(cloud_masks[image_idx])


all_cloud_masks = CloudMaskRequest(ogc_request=wms_bands_request, threshold=0.1)
fig = plt.figure(figsize=(15, 10))
n_cols = 4
n_rows = int(np.ceil(len(wms_true_color_imgs) / n_cols))

for idx, [prob, mask, data] in enumerate(all_cloud_masks):
    ax = fig.add_subplot(n_rows, n_cols, idx + 1)
    image = wms_true_color_imgs[idx]
    overlay_cloud_mask(image, mask, factor=1, fig=fig)

plt.tight_layout()


all_cloud_masks.get_dates()

fig = plt.figure(figsize=(15, 10))
n_cols = 4
n_rows = int(np.ceil(len(wms_true_color_imgs) / n_cols))

for idx, cloud_mask in enumerate(all_cloud_masks.get_cloud_masks(threshold=0.7)):
    ax = fig.add_subplot(n_rows, n_cols, idx + 1)
    plot_cloud_mask(cloud_mask, fig=fig)

plt.tight_layout()