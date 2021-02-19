import snappy
from snappy import ProductIO, HashMap, GPF, WKTReader, jpy
import numpy as np
from osgeo import gdal
import os
import glob
import datetime
import pandas as pd
import matplotlib.pyplot as plt


class sentinel1_lake_extraction(object):

    def __init__(self):
        self.process_path = r"/home/baris/Desktop/CE-STAR/Python_calisma_folder/Input/"
        self.lake_coordinates = r"/home/baris/Desktop/CE-STAR/Python_calisma_folder/WellKnownText/"
        self.output_folder = r"/home/baris/Desktop/CE-STAR/Python_calisma_folder/Output/"
        self.binary_output_folder = r"/home/baris/Desktop/CE-STAR/Python_calisma_folder/Output/Binary/"
        self.polygon_folder = r"/home/baris/Desktop/CE-STAR/Python_calisma_folder/Output/Shapefile/"
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
        files_found = sorted(list(glob.iglob(os.path.join(self.process_path, '**', '*S1*.zip'), recursive=True)))

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
        df_s1_read.to_excel("Images metadata.xlsx", sheet_name='Sentinel1')
        print(df_s1_read)
        self.product_name = df_s1_read['Name'].values.tolist()
        self.temporary_data_list = s1_read_list
        print('Data read is done!')

    def geo_subset(self):
        subset_list=[]
        lake_coordinates = os.path.join(self.lake_coordinates, 'mogan')
        data = open(lake_coordinates)
        data_string = data.read().replace("\n", " ")
        data.close()

        # snappy part
        for product in self.temporary_data_list:
            parameters = snappy.HashMap()
            parameters.put('copyMetadata', True)
            parameters.put('geoRegion', data_string)
            subset = snappy.GPF.createProduct("Subset", parameters, product)
            subset_list.append(subset)
            list(subset.getBandNames())
        self.temporary_data_list = subset_list
        print('Subsetting is done!')

    def thermal_noise_removel(self):
        thermal_noise_list = []
        for product in self.temporary_data_list:
            parameters = snappy.HashMap()
            parameters.put('removeThermalNoise', True)
            thermal_noise = snappy.GPF.createProduct("ThermalNoiseRemoval", parameters, product)
            thermal_noise_list.append(thermal_noise)
        self.temporary_data_list = thermal_noise_list
        print('Thermal noise removel is done!')

    def calibration(self):
        calibrated_list=[]
        for product in self.temporary_data_list:
            parameters = snappy.HashMap()
            parameters.put('outputSigmaBand', True)
            parameters.put('selectedPolarizations', 'VH,VV')
            parameters.put('outputImageScaleInDb', True)
            calibrated = snappy.GPF.createProduct("Calibration", parameters, product)
            calibrated_list.append(calibrated)
        print('Calibration is done!')
        self.temporary_data_list = calibrated_list

    def speckle_filter(self):
        speckle_filtered_list = []
        for product in self.temporary_data_list:
            parameters = snappy.HashMap()
            parameters.put('filter', 'Lee')
            speckle_filtered = snappy.GPF.createProduct('Speckle-Filter', parameters, product)
            speckle_filtered_list.append(speckle_filtered)
        self.temporary_data_list = speckle_filtered_list
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

        terrain_corrected_list = []
        for product in self.temporary_data_list:
            parameters = snappy.HashMap()
            parameters.put('demName', 'SRTM 1Sec HGT')
            parameters.put('imgResamplingMethod', 'BILINEAR_INTERPOLATION')
            parameters.put('pixelSpacingInMeter', 10.0)
            parameters.put('mapProjection', proj_wgs84_36n)
            parameters.put('nodataValueAtSea', False)
            parameters.put('saveSelectedSourceBand', True)
            terrain_corrected = snappy.GPF.createProduct('Terrain-Correction', parameters, product)
            terrain_corrected_list.append(terrain_corrected)

        print('Terrain correction is done!')
        self.temporary_data_list = terrain_corrected_list

    def write_product(self):
        self.temporary_raster_list =[]
        for product in self.temporary_data_list:
            string = (product).getName()
            output_name = os.path.join(self.output_folder, string)
            self.temporary_data = snappy.ProductIO.writeProduct(product, output_name, 'BEAM-DIMAP')
            self.temporary_raster_list.append(output_name + ".tif")

        print('Writing is done!')

    def write_tiff(self):
        self.temporary_raster_list = []
        for product in self.temporary_data_list:
            string = (product).getName()
            output_name = os.path.join(self.binary_output_folder, string)
            self.temporary_data = snappy.ProductIO.writeProduct(product, output_name, 'GeoTIFF')
            self.temporary_raster_list.append(output_name + ".tif")

        print('Writing is done!')


    def calculate_composite(self):

        pass

    def read_raster(self):
        self.current_crs_list = []
        self.current_raster_list = []
        for product in self.temporary_raster_list:
            raster_file = gdal.Open(product)
            self.current_srs = raster_file.GetGeoTransform()
            self.current_prj = raster_file.GetProjection()
            self.current_crs_list.append(raster_file.GetSpatialRef())
            self.current_raster_list.append(raster_file)
            raster_data = raster_file.GetRasterBand(1).ReadAsArray().astype(np.float32)
            self.current_raster_list.append(raster_data)

        self.temporary_raster_list = self.current_raster_list

    def calculate_threshold_from_tiff(self):

        for raster in self.temporary_raster_vv_list:
            raster_vv = raster
            start_time = datetime.datetime.now()
            plt.hist(raster_vv,range=(raster_vv.min()+2, raster_vv.max()-4), bins=20 )
            # show_hist(raster_vv,bins=512,lw=0.0, stacked=False, alpha=1, histtype='stepfilled', title="VV_dB Histogram")
            # show_hist(raster_vh, bins=512, lw=0.0, stacked=False, alpha=1, histtype='stepfilled', title="VH_dB Histogram")
            end_time = datetime.datetime.now()
            print(end_time-start_time,' second to generate histogram')
        plt.show()

    def apply_threshold_to_product(self):
        self.temporary_data_binary = []
        snappy.GPF.getDefaultInstance().getOperatorSpiRegistry().loadOperatorSpis()
        BandDescriptor = jpy.get_type('org.esa.snap.core.gpf.common.BandMathsOp$BandDescriptor')
        targetBand = BandDescriptor()
        targetBand.name = 'band1'
        targetBand.type = 'float32'
        targetBand.expression = 'Sigma0_VV_db < -20 '
        targetBands = jpy.array('org.esa.snap.core.gpf.common.BandMathsOp$BandDescriptor', 1)
        targetBands[0] = targetBand

        for product in self.decibel_list:
            parameters = snappy.HashMap()
            parameters.put('name', 'Sigma0_VV_db_Threshold')
            parameters.put('targetBands', targetBands)
            binary = snappy.GPF.createProduct('BandMaths', parameters, product)
            self.temporary_data_binary.append(binary)

        self.temporary_data_list = self.temporary_data_binary




    def convert_to_polygon(self):
        from osgeo import ogr, osr
        testSR = osr.SpatialReference()
        for current_crs in self.current_crs_list:
            testSR.ImportFromWkt(current_crs.ExportToWkt())
        binary_images = sorted(list(glob.iglob(os.path.join(self.binary_output_folder,'**', '*.tif'), recursive=True)))
        for product in binary_images:
            sourceRaster = gdal.Open(product)
            band = sourceRaster.GetRasterBand(1)
            bandArray = band.ReadAsArray()
            outShapefile = os.path.join(os.path.basename(str(product)))
            driver = ogr.GetDriverByName("ESRI Shapefile")
            output_file = os.path.join(self.polygon_folder,outShapefile+".shp")
            if os.path.exists(output_file):
                driver.DeleteDataSource(output_file)
            outDatasource = driver.CreateDataSource(output_file)
            outLayer = outDatasource.CreateLayer(str(outShapefile), srs = testSR)
            raster_value_field = ogr.FieldDefn('rasterVal', ogr.OFTInteger)
            outLayer.CreateField(raster_value_field)
            gdal.Polygonize(band,None,outLayer,0,[],callback=None)
            outDatasource.Destroy()
            sourceRaster=None


    def linear_to_dB(self):
        self.decibel_list = []
        for product in self.temporary_data_list:
            parameters = snappy.HashMap()
            parameters.put('sourceBands', 'Sigma0_VH,Sigma0_VV')
            decibel = GPF.createProduct("LinearToFromdB", parameters, product)
            self.decibel_list.append(decibel)
        self.temporary_data_list=self.decibel_list
        print("Linear to/from dB Conversion is done")


    def run_to_writing(self):

        self.traverse_data()
        self.read_data()
        self.terrain_correction()
        self.geo_subset()
        self.thermal_noise_removel()
        self.calibration()
        self.speckle_filter()
        self.linear_to_dB()
        self.write_product()
        print('Post processes of SAR Images is done!')

    def run_to_binarization_with_product(self):
        self.apply_threshold_to_product()
        self.write_tiff()
        self.read_raster()
        self.convert_to_polygon()
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
    sentinel1_lake_extraction_object.run_to_writing()
    sentinel1_lake_extraction_object.run_to_binarization_with_product()
    sentinel1_lake_extraction_object.end_time = datetime.datetime.now()
    # sentinel1_lake_extraction_object
    # lake_extraction_object.convert("lake_in_polygon", "lake_in_geojson")
    print("Process time:  {}".format(str(sentinel1_lake_extraction_object.end_time - sentinel1_lake_extraction_object.start_time)))
