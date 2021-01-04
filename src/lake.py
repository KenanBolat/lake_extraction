import os
import glob
import sys
import struct
import datetime
from osgeo import gdal
import numpy as np
import matplotlib.pyplot as plt
import rasterio
from shapely.geometry import shape, mapping
from shapely.geometry.multipolygon import MultiPolygon
import fiona
import rasterio.features

import functools

import fiona
import geojson
import pyproj
import shapely.geometry
import shapely.ops


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
        self.current_crs = None
        self.current_prj = None
        self.current_raster = None
        self.current_shape_folder = None

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
            self.current_crs = raster_file.GetSpatialRef()
            self.current_raster = raster_file

            raster_data = raster_file.GetRasterBand(1).ReadAsArray().astype(np.float32)
            raster_file = None
            return raster_data

        except BaseException as be:
            print(be)

    def convert(self, in_file, out_file):
        omit = ['SHAPE_AREA', 'SHAPE_LEN']
        f_in = os.path.join(self.process_path, self.output_folder, in_file + ".shp")
        f_out = os.path.join(self.process_path, self.output_folder, out_file + ".json")
        with fiona.open(f_in) as source:
            # Use the recipe from the Shapely documentation:
            # http://toblerity.org/shapely/manual.html
            project = functools.partial(pyproj.transform,
                                        pyproj.Proj(**source.crs),
                                        pyproj.Proj(init='epsg:4326'))

            features = []
            for f in source:
                shape = shapely.geometry.shape(f['geometry'])
                projected_shape = shapely.ops.transform(project, shape)

                # Remove the properties we don't want
                props = f['properties']  # props is a reference
                for k in omit:
                    if k in props:
                        del props[k]

                feature = geojson.Feature(id=f['id'],
                                          geometry=projected_shape,
                                          properties=props)
                features.append(feature)

        fc = geojson.FeatureCollection(features)

        with open(f_out, 'w') as f:
            f.write(geojson.dumps(fc))

    def export_index_to_raster(self, index, fname):

        drviver = gdal.GetDriverByName("GTiff")
        dataset_out = drviver.Create(os.path.join(self.process_path, self.output_folder, fname + ".tif"),
                                     self.current_raster.RasterXSize,
                                     self.current_raster.RasterYSize,
                                     1,
                                     gdal.GDT_Float32,
                                     options=["COMPRESS=LZW"])

        dataset_out.SetGeoTransform(self.current_srs)
        dataset_out.SetProjection(self.current_prj)
        out_band = dataset_out.GetRasterBand(1)
        out_band.WriteArray(index)
        dataset_out.FlushCache()
        dataset_out = None

    def convert_to_polygon(self, raster, polygon_file_name="lake"):

        from osgeo import ogr, osr
        testSR = osr.SpatialReference()
        testSR.ImportFromWkt(self.current_crs.ExportToWkt())

        sourceRaster = gdal.Open(os.path.join(self.process_path, self.output_folder, raster + ".tif"))
        band = sourceRaster.GetRasterBand(1)
        bandArray = band.ReadAsArray()
        outShapefile = polygon_file_name
        driver = ogr.GetDriverByName("ESRI Shapefile")
        output_file = os.path.join(self.process_path, self.output_folder, outShapefile + ".shp")
        if os.path.exists(output_file):
            driver.DeleteDataSource(output_file)
        outDatasource = driver.CreateDataSource(output_file)
        outLayer = outDatasource.CreateLayer(str(outShapefile), srs=testSR)
        raster_value_field = ogr.FieldDefn('rasterVal', ogr.OFTInteger)
        outLayer.CreateField(raster_value_field)
        gdal.Polygonize(band, None, outLayer, 0, [], callback=None)
        outDatasource.Destroy()
        sourceRaster = None



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

        self.export_index_to_raster(ndvi, "ndvi")
        self.export_index_to_raster(ndbi, "ndbi")
        self.export_index_to_raster(ndwi, "ndwi")
        self.export_index_to_raster(mndwi, "mndwi")

        lakes = (ndvi < 0) & (mndwi > 500) & (ndbi < 0)
        self.export_index_to_raster(lakes, "lakes")

if __name__ == '__main__':
    os.environ['GDAL_DATA'] = r'/usr/share/gdal'
    lake_extraction_object = lake_extraction()
    lake_extraction_object.export.run()
    lake_extraction_object.end_time = datetime.datetime.now()
    lake_extraction_object.convert_to_polygon("lakes", "lake_in_polygon_3")
    lake_extraction_object.convert("lake_in_polygon", "lake_in_geojson")
    print("Process time:  {}".format(str(lake_extraction_object.end_time - lake_extraction_object.start_time)))
