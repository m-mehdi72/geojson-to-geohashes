import os
import csv
import json
import geohash2 as geohash
import geopandas as gpd
import pygeohash as pgh
import geopandas as gpd
import pygeohash as pgh

def using_closest_point(geojson_file, geohash_precision):
    gdf = gpd.read_file(geojson_file)
    
    if 'name' not in gdf.columns:
        gdf['name'] = 'Unknown'
    
    gdf['closest_point'] = gdf.geometry.apply(lambda geom: geom.representative_point())
    gdf['geohash'] = gdf.closest_point.apply(lambda point: pgh.encode(point.y, point.x, precision=geohash_precision))
    
    return gdf[['name', 'geohash']].values.tolist()

def using_centroid(geojson_file, geohash_precision):
    gdf = gpd.read_file(geojson_file)
    
    if 'name' not in gdf.columns:
        gdf['name'] = 'Unknown'
    
    gdf['geohash'] = gdf.geometry.apply(lambda geom: pgh.encode(geom.centroid.y, geom.centroid.x, precision=geohash_precision))
    
    return gdf[['name', 'geohash']].values.tolist()


def convert_geojson_to_geohashes(geojson_file, precision):
    with open(geojson_file, 'r') as f:
        data = json.load(f)
    
    locations = []
    
    for feature in data['features']:
        geometry_type = feature['geometry']['type']
        properties = feature.get('properties', {})
        location_name = properties.get('name', '')  
        
        if geometry_type == 'Point':
            coords = feature['geometry']['coordinates']
            geohash_value = geohash.encode(coords[1], coords[0], precision=precision)
            locations.append((location_name, geohash_value))
        elif geometry_type == 'LineString' or geometry_type == 'Polygon':
            coords = feature['geometry']['coordinates']
            for coord in coords:
                for c in coord:
                    geohash_value = geohash.encode(c[1], c[0], precision=precision)
                    locations.append((location_name, geohash_value))
        elif geometry_type == 'MultiPoint' or geometry_type == 'MultiLineString' or geometry_type == 'MultiPolygon':
            if geometry_type == 'MultiPoint':
                coords = feature['geometry']['coordinates']
                for coord in coords:
                    geohash_value = geohash.encode(coord[1], coord[0], precision=precision)
                    locations.append((location_name, geohash_value))
            elif geometry_type == 'MultiLineString':
                for part in feature['geometry']['coordinates']:
                    for c in part:
                        geohash_value = geohash.encode(c[1], c[0], precision=precision)
                        locations.append((location_name, geohash_value))
            elif geometry_type == 'MultiPolygon':
                for part in feature['geometry']['coordinates']:
                    for sub_part in part:
                        for c in sub_part:
                            geohash_value = geohash.encode(c[1], c[0], precision=precision)
                            locations.append((location_name, geohash_value))
        else:
            print("Unsupported geometry type:", geometry_type)
    
    return locations

def sort_n_merge_lists(list1, list2, list3):
    merged_list = []

    if list1:
        merged_list.extend(list1)
    if list2:
        merged_list.extend(list2)
    if list3:
        merged_list.extend(list3)

    if merged_list:  # Check if merged_list is not empty
        merged_list.sort(key=lambda x: (x[0] if len(x) > 0 else None, x[1] if len(x) > 1 else None))
    
    return merged_list


def remove_duplicates(input_list):
    unique_items = []
    seen = set()
    for key, value in input_list:
        if (key, value) not in seen:
            unique_items.append((key, value))
            seen.add((key, value))
    return unique_items

def write_locations_and_geohashes_to_csv(locations, output_file):
    # with open(output_file, 'w') as f:
    #     for location_name, geohash_value in locations:
    #         f.write(f"{location_name}: {geohash_value}\n")

    with open(output_file, "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.writer(csvfile)
        for name, value in locations:
            writer.writerow([name, value])

def execute(file, precision=6):
    list1 = using_closest_point(file, precision)
    list2 = using_centroid(file, precision)
    list3 = convert_geojson_to_geohashes(file, precision)
    # list3=[]

    if list1 is None:
        list1 = []
    if list2 is None:
        list2 = []
    if list3 is None:
        list3 = []

    merged_list = sort_n_merge_lists(list1, list2, list3)

    clean_list = remove_duplicates(merged_list)

    return clean_list

path = 'Geojson_shapefiles'
geojson_files = os.listdir(path)

for file in geojson_files:
    if not file.startswith('.') and file.endswith('.geojson'):
        cur_path = f'{path}/{file}'
        file = file.split('.')[0]
        output_file = f'{file}.csv'
        geohashes = execute(cur_path)
    # print(type(geohashes))
    
    # for location_name, geohash_value in geohashes:
        # print(f"{location_name}: {geohash_value}")
        # print(f"{location_name}")

        write_locations_and_geohashes_to_csv(geohashes, output_file)

