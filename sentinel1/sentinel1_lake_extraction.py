import snappy
from snappy import ProductIO, HashMap, GPF, WKTReader, jpy
import numpy as np
from osgeo import gdal
import os
import glob
import gc
import datetime
import pandas as pd
import sys





class sentinel1_lake_extraction(object):

    def __init__(self):
        self.process_path     = r"/home/baris/Desktop/CE-STAR/Python_calisma_folder/Input/"
        self.lake_coordinates = r"/home/baris/Desktop/CE-STAR/Python_calisma_folder/WellKnownText/"
        self.output_folder    = r"/home/baris/Desktop/CE-STAR/Python_calisma_folder/Output/"
        self.start_time = datetime.datetime.now()
        self.end_time = None
        self.output_type = None
        self.lake_threshold = 0
        self.current_srs = None
        self.current_crs = None
        self.current_prj = None
        self.current_raster = None
        self.current_shape_folder = None
        self.temporary_data = None

    def check_process_folder(self):
        if not os.path.isdir(self.process_path): assert "Process Path does not exist!"

        return True



    def traverse_data(self):
        files_found =   sorted(list(glob.iglob(os.path.join(self.process_path,'**', '*S1*.zip'), recursive=True)))

        self.temporary_data = files_found
        print('Images are found')



    def read_data(self):
        name, sensing_mode, product_type, polarization, height, width, band_names = ([] for i in range(7))
        s1_read_list = []

        for i in self.temporary_data:
            sensing_mode.append(i.split("_")[3])
            product_type.append(i.split("_")[4])
            polarization.append(i.split("_")[-6])
            # reading products with snappy library
            s1_products = snappy.ProductIO.readProduct(i)
            name.append(s1_products.getName())
            height.append(s1_products.getSceneRasterHeight())
            width.append(s1_products.getSceneRasterWidth())
            band_names.append(s1_products.getBandNames())
            s1_read_list.append(s1_products)

        df_s1_read = pd.DataFrame(
            {'Name': name, 'Sensing Mode': sensing_mode, 'Product Type': product_type, 'Polarization': polarization,
             'Height': height, 'Width': width, 'Band Names': band_names})
        df_s1_read.to_excel("Images metadata.xlsx",sheet_name='Sentinel1')
        print(df_s1_read)
        self.product_name = df_s1_read['Name'].values.tolist()
        self.temporary_data = s1_products
        print('Data read is done!')




    def geo_subset(self):
        lake_coordinates = os.path.join(self.lake_coordinates,'uyuz')
        data = open(lake_coordinates)
        data_string = data.read().replace("\n"," ")
        data.close()

        #snappy part
        parameters = snappy.HashMap()
        parameters.put('copyMetadata', True)
        parameters.put('geoRegion', data_string)
        subset = snappy.GPF.createProduct("Subset", parameters, self.temporary_data )
        list(subset.getBandNames())
        self.temporary_data = subset
        print('Subsetting is done!')


    def thermal_noise_removel(self):
        parameters = snappy.HashMap()
        parameters.put('removeThermalNoise', True)
        thermal_noise = snappy.GPF.createProduct("ThermalNoiseRemoval", parameters,self.temporary_data)
        self.temporary_data = thermal_noise
        print('Thermal noise removel is done!')


    def calibration(self):
        parameters = snappy.HashMap()
        parameters.put('outputSigmaBand', True)
        parameters.put('selectedPolarizations', 'VH,VV' )
        parameters.put('outputImageScaleInDb', True)
        calibrated = snappy.GPF.createProduct("Calibration", parameters, self.temporary_data)
        print('Calibration is done!')
        self.temporary_data = calibrated

    def speckle_filter(self):
        parameters = snappy.HashMap()
        parameters.put('filter', 'Lee')
        speckle_filtered = snappy.GPF.createProduct('Speckle-Filter',parameters,self.temporary_data)
        self.temporary_data= speckle_filtered
        print('Speckle filtering is done!')



    def terrain_correction(self):

        proj_wgs84 = '''GEOGCS["WGS 84",
    DATUM["WGS_1984",
        SPHEROID["WGS 84",6378137,298.257223563,
            AUTHORITY["EPSG","7030"]],
        AUTHORITY["EPSG","6326"]],
    PRIMEM["Greenwich",0,
        AUTHORITY["EPSG","8901"]],
    UNIT["degree",0.01745329251994328,
        AUTHORITY["EPSG","9122"]],
    AUTHORITY["EPSG","4326"]]'''
        proj_wgs84_36n = '''PROJCS["WGS 84 / UTM zone 36N",
    GEOGCS["WGS 84",
        DATUM["WGS_1984",
            SPHEROID["WGS 84",6378137,298.257223563,
                AUTHORITY["EPSG","7030"]],
            AUTHORITY["EPSG","6326"]],
        PRIMEM["Greenwich",0,
            AUTHORITY["EPSG","8901"]],
        UNIT["degree",0.0174532925199433,
            AUTHORITY["EPSG","9122"]],
        AUTHORITY["EPSG","4326"]],
    PROJECTION["Transverse_Mercator"],
    PARAMETER["latitude_of_origin",0],
    PARAMETER["central_meridian",33],
    PARAMETER["scale_factor",0.9996],
    PARAMETER["false_easting",500000],
    PARAMETER["false_northing",0],
    UNIT["metre",1,
        AUTHORITY["EPSG","9001"]],
    AXIS["Easting",EAST],
    AXIS["Northing",NORTH],
    AUTHORITY["EPSG","32636"]]'''
        proj_wgs84_35n = '''PROJCS["WGS 84 / UTM zone 35N",
    GEOGCS["WGS 84",
        DATUM["WGS_1984",
            SPHEROID["WGS 84",6378137,298.257223563,
                AUTHORITY["EPSG","7030"]],
            AUTHORITY["EPSG","6326"]],
        PRIMEM["Greenwich",0,
            AUTHORITY["EPSG","8901"]],
        UNIT["degree",0.0174532925199433,
            AUTHORITY["EPSG","9122"]],
        AUTHORITY["EPSG","4326"]],
    PROJECTION["Transverse_Mercator"],
    PARAMETER["latitude_of_origin",0],
    PARAMETER["central_meridian",27],
    PARAMETER["scale_factor",0.9996],
    PARAMETER["false_easting",500000],
    PARAMETER["false_northing",0],
    UNIT["metre",1,
        AUTHORITY["EPSG","9001"]],
    AXIS["Easting",EAST],
    AXIS["Northing",NORTH],
    AUTHORITY["EPSG","32635"]]'''


        parameters = snappy.HashMap()
        parameters.put('demName', 'SRTM 1Sec HGT')
        parameters.put('imgResamplingMethod', 'BILINEAR_INTERPOLATION')
        parameters.put('pixelSpacingInMeter',10.0)
        parameters.put('mapProjection', proj_wgs84_36n)
        parameters.put('nodataValueAtSea', False)
        parameters.put('saveSelectedSourceBand', True)
        terrain_corrected = snappy.GPF.createProduct('Terrain-Correction',parameters,self.temporary_data)
        print('Terrain correction is done!')
        self.temporary_data = terrain_corrected

    def write_product(self):
        string = (self.temporary_data).getName()

        output_name = os.path.join(self.output_folder,string)
        self.temporary_data = snappy.ProductIO.writeProduct(self.temporary_data, output_name, 'BEAM-DIMAP')
        self.temporary_raster = output_name + ".tif"
        print('Writing is done!')


    def calculate_composite(self):

        pass

    def read_raster(self):

        raster_file = gdal.Open(self.temporary_raster)
        self.current_srs = raster_file.GetGeoTransform()
        self.current_prj = raster_file.GetProjection()
        self.current_crs = raster_file.GetSpatialRef()
        self.current_raster = raster_file
        raster_data_vv = raster_file.GetRasterBand(2).ReadAsArray().astype(np.float32)
        raster_data_vh = raster_file.GetRasterBand(1).ReadAsArray().astype(np.float32)
        self.temporary_raster_vv = raster_data_vv
        self.temporary_raster_vh = raster_data_vh


    def calculate_threshold(self):
#         raster_vv = self.temporary_raster_vv
#         raster_vh = self.temporary_raster_vh
#         start_time = datetime.datetime.now()
#         hist, bin_edges = np.histogram(raster_vv, bins=512)
#         if is_normalized:            9
#             hist = np.divide(hist.ravel(), hist.max())
#
#         bin_mids = (bin_edges[:-1] + bin_edges[1:]) / 2.
#
# # show_hist(raster_vv,bins=512,lw=0.0, stacked=False, alpha=1, histtype='stepfilled', title="VV_dB Histogram")
#         # show_hist(raster_vh, bins=512, lw=0.0, stacked=False, alpha=1, histtype='stepfilled', title="VH_dB Histogram")
#
#         end_time = datetime.datetime.now()
#         print(end_time-start_time,' second to generate histogram')
        pass


    def threshold_to_raster(self):
        pass

    def convert_to_polygon(self):
        pass


    def linear_to_dB(self):
        parameters = snappy.HashMap()
        parameters.put('sourceBands', 'Sigma0_VH,Sigma0_VV')
        decibel = GPF.createProduct("LinearToFromdB", parameters, self.temporary_data)
        print("Linear to/from dB Conversion is done")
        self.temporary_data=decibel

    def run(self):

        self.traverse_data()
        self.read_data()
        self.thermal_noise_removel()
        self.calibration()
        self.speckle_filter()
        self.terrain_correction()
        self.linear_to_dB()
        self.geo_subset()
        self.write_product()



    @property
    def as_int(self):
        self.output_type = "int"
        return self

    @property
    def as_float(self):
        self.output_type = "float"
        return self

    @property
    def export(self):
        self.export_files = True
        return self



if __name__ == '__main__':
    sentinel1_lake_extraction_object = sentinel1_lake_extraction()
    sentinel1_lake_extraction_object.run()
    sentinel1_lake_extraction_object.end_time = datetime.datetime.now()
    # lake_extraction_object.convert_to_polygon("lakes", "lake_in_polygon_3")
    # lake_extraction_object.convert("lake_in_polygon", "lake_in_geojson")
    print("Process time:  {}".format(str(sentinel1_lake_extraction_object.end_time - sentinel1_lake_extraction_object.start_time)))
