import snappy
from snappy import ProductIO, HashMap, GPF, WKTReader, jpy
import os
import glob
import gc
import datetime
import pandas as pd
import sys


class sentinel1_lake_extraction(object):

    def __init__(self):
        self.process_path = r"/home/baris/Desktop/CE-STAR/rapor_burdur/2018_2020/"
        self.lake_coordinates =   r"/home/baris/PycharmProjects/sentinel1/WellKnownText/"
        # self.output.folder          = # output folder
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

        return (files_found)

    def read_data(self, file_):
        name, sensing_mode, product_type, polarization, height, width, band_names = ([] for i in range(7))
        s1_read_list = []
        for i in file_:
            sensing_mode.append(i.split("_")[3])
            product_type.append(i.split("_")[4])
            polarization.append(i.split("_")[-6])
            # read with snappy library
            s1_products= snappy.ProductIO.readProduct(i)
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
        self.temporary_data = df_s1_read
        self.temporary_data_read = s1_read_list




    def subset(self):
        karatas_coordinates = os.path.join(self.lake_coordinates,'karatas')
        with open(karatas_coordinates , "r") as myfile:
            data = ''
            data = myfile.readlines()
            data = "".join(data)
        print("Karatas Geo-Location: " ,data)
        subset_list = []
        #snappy part
        parameters = snappy.HashMap()
        parameters.put('copyMetadata', True)
        parameters.put('geoRegion', data)
        subsetted_images = snappy.GPF.createProduct("Subset", parameters, self.temporary_data_read )



        print(subset_list)
        a = 1


    def calibration(self):
        self.temporary_data = data_
        pass

    def speckle_filter(self):

        self.temporary_data = data_
        pass

    def terrain_correction(self):
        pass

    def calculate_composite(self, VV_db, VH_db):
        pass

    def calculate_threshold(self):
        pass

    def threshold_to_raster(self):
        pass

    def selfconvert_to_polygon(self):
        pass

    def back_scattering(self, data_):
        pass
        self.read_data(data_)
        self.subset(data_)
        self.calibration(data_)
        self.speckle_filter(data_)
        self.terrain_correction(data_)

    def run(self):

        images_name = self.traverse_data()
        images = self.read_data(images_name)
        kozanli = self.subset()


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
    # lake_extraction_object.end_time = datetime.datetime.now()
    # lake_extraction_object.convert_to_polygon("lakes", "lake_in_polygon_3")
    # lake_extraction_object.convert("lake_in_polygon", "lake_in_geojson")
    # print("Process time:  {}".format(str(lake_extraction_object.end_time - lake_extraction_object.start_time)))
