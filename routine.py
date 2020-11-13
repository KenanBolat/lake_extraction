import os
import glob
import datetime
import arcpy
import numpy as np
import matplotlib.pyplot as plt

# import gdal
arcpy.env.overwriteOutput = True


class lake_extraction(object):
    def __init__(self):
        self.process_path = r"C:\lake_extraction_data"
        self.start_time = datetime.datetime.now()
        self.end_time = None
        self.output_type = None
        self.scale_factor = 1000
        self.lake_threshold = 0
        self.export_files = False
        arcpy.env.workspace = self.process_path

    def traverse_data(self, pattern="RT_*.tif"):
        files = []
        for file_ in glob.glob1(self.process_path, pattern):
            files.append(os.path.join(self.process_path, file_))
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

    def calculate_ndvi(self, band_1, band_3):

        numerator = arcpy.sa.Float(band_1 - band_3)
        denominator = arcpy.sa.Float(band_1 + band_3)
        if self.output_type == "int":
            return arcpy.sa.Int(arcpy.sa.Divide(numerator, denominator) * self.scale_factor)
        else:
            return arcpy.sa.Float(arcpy.sa.Divide(numerator, denominator))

    def calculate_ndwi(self, band_nir, band_swir):

        numerator = arcpy.sa.Float(band_nir - band_swir)
        denominator = arcpy.sa.Float(band_nir + band_swir)
        if self.output_type == "int":
            return arcpy.sa.Int(arcpy.sa.Divide(numerator, denominator) * self.scale_factor)
        else:
            return arcpy.sa.Float(arcpy.sa.Divide(numerator, denominator))

    def read_data(self, file_):
        try:
            raster_file = arcpy.Raster(file_)
            print("File Has been read:  {}".format(file_))
            return raster_file
        except BaseException as be:
            print(be)

    def run(self):
        print("Process has been started at {} ".format(self.start_time))
        files = self.traverse_data()

        band_4 = self.read_data(files[1])
        band_3 = self.read_data(files[0])

        # Calculate ndwi
        ndwi_int = self.as_int.calculate_ndwi(band_4, band_3)

        # Apply Threshold
        lake_raster = arcpy.sa.Con(ndwi_int < self.lake_threshold, 1, 0)

        # Convert To polygon
        arcpy.RasterToPolygon_conversion(lake_raster,
                                         os.path.join(self.process_path, "lake_polygon.shp"),
                                         "NO_SIMPLIFY",
                                         "VALUE")

        if self.export_files:
            ndwi_int.save(os.path.join(self.process_path, "ndvi_int.tif"))
            lake_raster.save(os.path.join(self.process_path, "lake_raster.tif"))
        # Flaat Example
        # output_file_name_flt = "ndvi_flt.tif"
        # ndvi_float = self.as_float.calculate_ndvi(band_4, band_3)
        # ndvi_float.save(os.path.join(self.process_path, output_file_name_flt))


if __name__ == '__main__':
    lake_extraction_object = lake_extraction()
    lake_extraction_object.export.run()
    lake_extraction_object.end_time = datetime.datetime.now()
    print("Process time:  {}".format(str(lake_extraction_object.end_time - lake_extraction_object.start_time)))
