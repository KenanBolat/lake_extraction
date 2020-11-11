import os
import glob
import datetime
import arcpy
import numpy as np
import matplotlib.pyplot as plt
import gdal
arcpy.env.overwriteOutput = True




class lake_extraction(object):
    def __init__(self):
        self.process_path = r"C:\lake_extraction_data"
        self.start_time = datetime.datetime.now()
        self.end_time = None
        arcpy.env.workspace = self.process_path

    def traverse_data(self, pattern="*.tif"):
        files = []
        for file_ in glob.glob1(self.process_path, pattern):
            files.append(os.path.join(self.process_path, file_))
        if len(files) <= 0:
            assert "There are no files within the specified folder"
        else:
            return files

    def calculate_ndvi(self, band_1, band_3, scale_factor=10000):

        numerator = arcpy.sa.Float(band_1 - band_3)
        denumerator = arcpy.sa.Float(band_1 + band_3)


        return arcpy.sa.Divide(numerator, denumerator)
        # return (band_1 - band_3)

    def read_data(self, file_):
        try:
            files = self.traverse_data()
            raster_file = arcpy.Raster(file_)
            print("File Has been read {}".format(1))
            return raster_file

        except BaseException as be:
            print(be)

    def run(self):
        print("Process has been started at {} ".format(self.start_time))
        files = self.traverse_data()
        band_1 = self.read_data(files[1])
        band_3 = self.read_data(files[0])
        ndvi = self.calculate_ndvi(band_1, band_3)
        ndvi.save(r"C:\lake_extraction_data\sil_3.tif")
        pass


if __name__ == '__main__':
    l_e = lake_extraction()
    l_e.run()
    print(l_e.process_path);
