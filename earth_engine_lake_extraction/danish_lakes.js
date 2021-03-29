// version = 0.0.2
// App = https://oztasbaris12.users.earthengine.app/view/danish-lakes

<<<<<<< HEAD
var L8 = ee.ImageCollection("LANDSAT/LC08/C01/T1_SR"),
    dataset = ee.FeatureCollection("USDOS/LSIB_SIMPLE/2017"),
    rgb_vis = {"opacity":1,"bands":["B4","B3","B2"],"min":-607.027817603207,"max":1474.2185690482938,"gamma":1},
    mndwi_vis = {"opacity":1,"bands":["MNDWI"],"palette":["ff0000","1000ff"]},
    ndvi_vis = {"opacity":1,"bands":["NDVI"],"palette":["ff0000","ffa500","00ff14"]},
    mask = ee.FeatureCollection("users/oztasbaris12/Danish_lakes/Mask_shapefile/danish_mask"),
    table2 = ee.FeatureCollection("users/oztasbaris12/Danish_lakes/Mask_shapefile/danish_samples"),
    sentinel1 = ee.FeatureCollection("users/oztasbaris12/Sentinel1/Denmark/S1_20150503"),
    S1 = ee.ImageCollection("COPERNICUS/S1_GRD"),
    vh_vis = {"opacity":1,"bands":["VH"],"min":-29.920891753796575,"max":-12.726552611079589,"gamma":1},
    vv_vis = {"opacity":1,"bands":["VV"],"min":-21.733165202492494,"max":9.709049077231972,"gamma":1};

=======
>>>>>>> parent of ab5a140 (Update danish_lakes.js)
function area_of_interest(dataset, string){
	var aoi = dataset.filter(ee.Filter.eq('country_na', string));
	Map.centerObject(aoi,7.3);
	return aoi
}
function filtering_image_collection(image_dataset, mask, cloud_cover, start_date, end_date){
	var image_dataset = L8.filterBounds(mask)
.filterMetadata('CLOUD_COVER_LAND', 'less_than', cloud_cover)
.filterDate(start_date, end_date);
	print('Size of filtered data is', image_dataset.size())
	return image_dataset
}
function median(image_dataset) {
	var median_image = image_dataset.median();
	return median_image
}
function add_symbology(image, parameters, string, shown){
	Map.addLayer(image, parameters, string, shown);
}
function MNDWI_NDVI_composite (NDVI, MNDWI, water_threshold, vegatation_threshold){
	var binary = MNDWI.gte(water_threshold).and(NDVI.lte(vegatation_threshold));
	return binary
}
function polygonize(image, mask){
  var lake_polygon = image.reduceToVectors({
    geometry: mask,
  crs: 'EPSG:32632',
  scale:7
  })
  return lake_polygon
}

var start_date  = "2020-05-01";
var end_date    = "2020-05-31";
var cloud_cover = 50;
var aoi = 'Denmark';
var denmark = area_of_interest(dataset, aoi);
var filtered_image_collection = filtering_image_collection(L8,mask, 50, "2020-01-01", "2020-12-31");
print(filtered_image_collection)
var median_image = median(filtered_image_collection);
var MNDWI = median_image.normalizedDifference(['B3','B6']).rename('MNDWI');
var NDVI = median_image.normalizedDifference(['B5','B4']).rename('NDVI');
var binary = MNDWI_NDVI_composite(NDVI,MNDWI, 0, 0);
var lake_polygon = polygonize(binary.clip(mask), mask);



var controlPanel = ui.Panel({
  style: {width: '400px', position: 'top-left'} //, backgroundColor: 'rgba(255, 255, 255, 0)'
});

ui.root.add(controlPanel);

var instructionsLabel= ui.Label('Readme & About',{fontWeight: 'bold'});
var instructions= ui.Label(
  "This Earth Engine App is extracting water bodies \n"+
  "from Landsat 8 - Sentinel 1/2 images.\n"+
  "Note: Sentinel 1/2 is not implemented yet."+
  "\n\n"+
  "Thşngs that Will be available soon:\n\n"+
  "1. Charts for area change over years(1984-2020)\n"+
  "2. Clickable lake objects for more information\n"+
  "...about that lake.\n"+
  "3. Select RGB/band display combination\n"+
  "4. More area of interest. (Turkey Lakes - Danish Lakes)\n"+
  "5. Water occurence over years for desired pixel or area\n"+
  "6. Widget for threshold selection for NDVI AND MNDWI"+
  "\n\n"+
  "This app designed for Saline Lakes project.\n\n"+
  "\n\n"+
  "Choose cloud score from slider(0-100):"+ 
  "\n(NOT AVAILABLE RIGHT NOW)"
  , {whiteSpace:'pre'}
);
var instructionsPanel = ui.Panel([instructionsLabel,instructions]);

var button = ui.Button({
  label: 'Calculate areas for desired parameters(NOT WORKING ATM)',
  onClick: function() {
    print("Calculating...");
  }
});


var checkbox_median = ui.Checkbox('Show True Color Composite for given date range', true);

checkbox_median.onChange(function(checked) {
  // Shows or hides the first map layer based on the checkbox's value.
  Map.layers().get(3).setShown(checked);
});



var checkbox_ndvi = ui.Checkbox('Show NDVI layer', true);

checkbox_ndvi.onChange(function(checked) {
  // Shows or hides the first map layer based on the checkbox's value.
  Map.layers().get(1).setShown(checked);
});



var checkbox_mndwi = ui.Checkbox('Show MNDWI layer', true);

checkbox_mndwi.onChange(function(checked) {
  // Shows or hides the first map layer based on the checkbox's value.
  Map.layers().get(2).setShown(checked);
});



var checkbox_binary = ui.Checkbox('Show Binary layer', false);

checkbox_binary.onChange(function(checked) {
  // Shows or hides the first map layer based on the checkbox's value.
  Map.layers().get(0).setShown(checked);
});



var checkbox_lake_polygons = ui.Checkbox('Show Landsat8 Polygons', true);

checkbox_lake_polygons.onChange(function(checked) {
  // Shows or hides the first map layer based on the checkbox's value.
  Map.layers().get(4).setShown(checked);
});

var cloud_cover_slider = ui.Slider({
	min: 0, max: 100, step: 1, value: 50,
	style: {stretch: 'horizontal', width: '300px' },
	onChange:function(value){
		cloud_cover = value;
	},
	disabled:true
	});
// cloud_cover_slider.setValue(10); // Default cloud cover score
// cloud_cover_slider.onChange(function(value) {
//	cloud_cover = value;
//	}); 



controlPanel.add(instructionsPanel);
controlPanel.add(cloud_cover_slider);
controlPanel.add(checkbox_median);
controlPanel.add(checkbox_mndwi);
controlPanel.add(checkbox_ndvi);
controlPanel.add(checkbox_binary);
controlPanel.add(checkbox_lake_polygons);
controlPanel.add(button)

add_symbology(binary, null, 'Binary Image', 0)
add_symbology(NDVI, ndvi_vis, 'NDVI', 1);
add_symbology(MNDWI, mndwi_vis, 'MNDWI', 1);
add_symbology(median_image, rgb_vis, 'Median Image',1);
add_symbology(lake_polygon, null, 'Lake Polygons',1)
Map.addLayer(table2, {color: 'FF0000'}, 'Lake Dataset');
Map.addLayer(sentinel1, {color: '0000FF'}, 'Sentinel 1 Lake Polygons')

//////////////////////////// SENTINEL1 PART ////////////////////////////////

var sar_filtered_vv = S1
  // Filter to get images with VV and VH dual polarization.
  .filter(ee.Filter.listContains('transmitterReceiverPolarisation', 'VV'))
  .filter(ee.Filter.listContains('transmitterReceiverPolarisation', 'VH'))
  // Filter to get images collected in interferometric wide swath mode.
  .filter(ee.Filter.eq('instrumentMode', 'IW'))
  .filterBounds(denmark).filterDate("2020-05-01", "2020-05-31")
  .select("VV");
  
var sar_filtered_vh = S1
// Filter to get images with VV and VH dual polarization.
.filter(ee.Filter.listContains('transmitterReceiverPolarisation', 'VV'))
.filter(ee.Filter.listContains('transmitterReceiverPolarisation', 'VH'))
// Filter to get images collected in interferometric wide swath mode.
.filter(ee.Filter.eq('instrumentMode', 'IW'))
.filterBounds(denmark).filterDate("2020-05-01", "2020-05-31")
.select("VH");
  


// Display as a composite of polarization and backscattering characteristics.

Map.addLayer(sar_filtered_vv,vv_vis,'Polarization: VV_db');
Map.addLayer(sar_filtered_vh,vh_vis, 'Polarization: VH_db')


var checkbox_vv = ui.Checkbox('Show VV Polarization', true);

checkbox_vv.onChange(function(checked) {
  // Shows or hides the first map layer based on the checkbox's value.
  Map.layers().get(7).setShown(checked);
});


var checkbox_vh = ui.Checkbox('Show VH Polarization', true);

checkbox_vh.onChange(function(checked) {
  // Shows or hides the first map layer based on the checkbox's value.
  Map.layers().get(8).setShown(checked);
});

var checkbox_s1_polygons = ui.Checkbox('Show Sentinel 1 Polygon', true);

checkbox_s1_polygons.onChange(function(checked) {
  // Shows or hides the first map layer based on the checkbox's value.
  Map.layers().get(6).setShown(checked);
});


controlPanel.add(checkbox_vh)
controlPanel.add(checkbox_vv)
controlPanel.add(checkbox_s1_polygons)

