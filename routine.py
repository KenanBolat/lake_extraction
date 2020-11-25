import os
import glob
import sys
import struct
import datetime
from osgeo import gdal
import numpy as np
import matplotlib.pyplot as plt


class lake_extraction(object):
    def __init__(self):
        self.process_path = r"/home/knn/Desktop/lake_extraction"
        self.input_folder = "input"
        self.output_folder = "output"
        self.start_time = datetime.datetime.now()
        self.end_time = None
        self.output_type = None
        self.scale_factor = 1000
        self.lake_threshold = 0
        self.export_files = False
        self.current_srs = None
        self.current_prj = None

    def check_process_folder(self):
        if not os.path.isdir(self.process_path): assert "Process Path does not exist!"
        return True

    def check_folder(self, folder):
        if self.check_process_folder():
            if not os.path.isdir(os.path.join(self.process_path, folder)):
                os.mkdir(os.path.join(self.process_path, folder))
        else:
            return False
        return True

    def traverse_data(self, pattern="RT_*.TIF"):
        files = []
        if self.check_folder(self.input_folder):
            for file_ in glob.glob1(os.path.join(self.process_path, self.input_folder), pattern):
                files.append(os.path.join(self.process_path, self.input_folder, file_))
        if len(files) <= 0:
            assert "There are no files within the specified folder"
        else:
            return files

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

    def calculate_ndwi(self, band_nir, band_swir):
        # For Landsat 7 NDWI =  (Band 4 – Band 5) / (Band 4 + Band 5)
        # For Landsat 8 NDWI =  (Band 5 – Band 6) / (Band 5 + Band 6)

        numerator = (band_nir - band_swir)
        denominator = (band_nir + band_swir)
        return (numerator / denominator) * self.scale_factor

    def calculate_mndwi(self, green, band_swir):
        # For Landsat 7 NDWI =  (Band 2 – Band 5) / (Band 2 + Band 5)
        # For Landsat 8 NDWI =  (Band 3 – Band 6) / (Band 3 + Band 6)

        numerator = (green - band_swir)
        denominator = (green + band_swir)
        return (numerator / denominator) * self.scale_factor


    def calculate_ndvi(self, band_nir, band_red):
        # For Landsat 7 NDVI = (Band 4 – Band 3) / (Band 4 + Band 3)
        # For Landsat 8 NDVI = (Band 5 – Band 4) / (Band 5 + Band 4)
        # NDVI = -1 to 0 represent Water bodies

        numerator = (band_nir - band_red)
        denominator = (band_nir + band_red)
        return (numerator / denominator) * self.scale_factor

    def calculate_ndbi(self, band_swir, band_nir):
        # For Landsat 7 NDBI = (Band 5 – Band 4) / (Band 5 + Band 4)
        # For Landsat 8 NDBI = (Band 6 – Band 5) / (Band 6 + Band 5)
        # NDBI = -1 to 0 represent Water bodies
        numerator = (band_swir - band_nir)
        denominator = (band_swir + band_nir)
        return (numerator / denominator) * self.scale_factor



    def read_data(self, file_):
        try:
            raster_file = gdal.Open(file_)
            self.current_srs = raster_file.GetGeoTransform()
            self.current_prj = raster_file.GetProjection()

            raster_data = raster_file.GetRasterBand(1).ReadAsArray().astype(np.float32)
            raster_file = None
            return raster_data

        except BaseException as be:
            print(be)

    def run(self):
        print("Process has been started at {} ".format(self.start_time))
        # files = self.traverse_data("*B4*.TIF")
        band_2_fname = self.traverse_data("*B2*.TIF")[0]
        band_3_fname = self.traverse_data("*B3*.TIF")[0]
        band_4_fname = self.traverse_data("*B4*.TIF")[0]
        band_5_fname = self.traverse_data("*B5*.TIF")[0]

        band_2 = self.read_data(band_2_fname)
        band_3 = self.read_data(band_3_fname)
        band_4 = self.read_data(band_4_fname)
        band_5 = self.read_data(band_5_fname)

        # Calculate indices

        ndvi = self.calculate_ndvi(band_4, band_3)
        ndwi = self.calculate_ndwi(band_4, band_5)
        ndbi = self.calculate_ndbi(band_5, band_4)
        mndwi = self.calculate_mndwi(band_2, band_5)

        a = ndvi <0 ;
        b = ndvi <0 ;
        pass
        # Apply Threshold
        # lake_raster = arcpy.sa.Con(ndwi_int < self.lake_threshold, 1, 0)

        # Convert To polygon
        # arcpy.RasterToPolygon_conversion(lake_raster,
        #                                  os.path.join(self.process_path, "lake_polygon.shp"),
        #                                  "NO_SIMPLIFY",
        #                                  "VALUE")

        if self.export_files:
            # ndwi_int.save(os.path.join(self.process_path, "ndvi_int.tif"))
            # lake_raster.save(os.path.join(self.process_path, "lake_raster.tif"))
            pass
        # Flaat Example
        # output_file_name_flt = "ndvi_flt.tif"
        # ndvi_float = self.as_float.calculate_ndvi(band_4, band_3)
        # ndvi_float.save(os.path.join(self.process_path, output_file_name_flt))


if __name__ == '__main__':
    lake_extraction_object = lake_extraction()
    lake_extraction_object.export.run()
    lake_extraction_object.end_time = datetime.datetime.now()
    print("Process time:  {}".format(str(lake_extraction_object.end_time - lake_extraction_object.start_time)))
