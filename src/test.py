from sentinelhub import SHConfig
import json
from shapely.geometry import shape

CLIENT_ID = '9f7a0f53-d397-46ec-bc2c-7d109acc1dce'
CLIENT_SECRET = 'J<2/_MJx9G,wf5n+U6q,mls[hga>nK-LTHjRi!p/'

config = SHConfig()

config.instance_id = 'ebb43985-6aca-476b-9719-fce4e7a54d60'

import datetime
import numpy as np
import matplotlib.pyplot as plt

from sentinelhub import WmsRequest, WcsRequest, MimeType, CRS, BBox, DataCollection


def plot_image(image, factor=1):
    """
    Utility function for plotting RGB images.
    """
    fig = plt.subplots(nrows=1, ncols=1, figsize=(15, 7))

    if np.issubdtype(image.dtype, np.floating):
        plt.imshow(np.minimum(image * factor, 1))
    else:
        plt.imshow(image)


def get_bbox(polygon, inflate_bbox=0.1):
    """
    Determines the BBOX from polygon. BBOX is inflated in order to include polygon's surroundings.
    """
    minx, miny, maxx, maxy = polygon.bounds
    delx = maxx - minx
    dely = maxy - miny

    minx = minx - delx * inflate_bbox
    maxx = maxx + delx * inflate_bbox
    miny = miny - dely * inflate_bbox
    maxy = maxy + dely * inflate_bbox

    return BBox(bbox=[minx, miny, maxx, maxy], crs=CRS.WGS84)


betsiboka_coords_wgs84 = [46.16, -16.15, 46.51, -15.58]
betsiboka_bbox = BBox(bbox=betsiboka_coords_wgs84, crs=CRS.WGS84)

# wms_true_color_request = WmsRequest(
#     data_collection=DataCollection.SENTINEL2_L1C,
#     layer='TRUE-COLOR-S2-L1C',
#     bbox=betsiboka_bbox,
#     time='2017-12-15',
#     width=512,
#     height=856,
#     config=config
# )

# get water polygon
file = '/home/cak/Desktop/lake_extraction/water_observe/data/data.geojson'
# water_polygon = gpd.read_file(file)

with open(file) as f:
    data = json.load(f)

nominal_outline = shape(data['features'][0]['geometry'])
the_dam_bbox = get_bbox(nominal_outline)
# resx, resy = get_optimal_resolution(the_dam_bbox)

wms_true_color_request = WmsRequest(
    data_collection=DataCollection.SENTINEL2_L1C,
    layer='NDVI',
    bbox=the_dam_bbox,
    time='2019-06-20',
    width=512,
    height=856,
    maxcc=0.5,
    image_format=MimeType.TIFF_d32f,
    config=config,
    data_folder='.'
)
wms_true_color_request = WmsRequest(
    data_collection=DataCollection.SENTINEL2_L1C,
    layer='NDVI',
    bbox=the_dam_bbox,
    time='2019-06-20',
    width=512,
    height=856,
    maxcc=0.5,
    image_format=MimeType.TIFF_d32f,
    config=config,
    data_folder='.'
)

wcs_ndwi_request = WcsRequest(
    data_collection=DataCollection.SENTINEL2_L1C,
    layer='NDWI',
    bbox=the_dam_bbox,
    time='latest',
    maxcc=0.5,
    resx='20m',
    resy='20m',
    image_format=MimeType.TIFF_d32f,
    # time_difference=timedelta(hours=2),
    # custom_url_params={CustomUrlParam.SHOWLOGO: False,
    #                    CustomUrlParam.TRANSPARENT: True},
    config=config,
    data_folder='.')

wms_true_color_img = wcs_ndwi_request.get_data(save_data=True)
wms_true_color_img = wms_true_color_request.get_data(save_data=True)
