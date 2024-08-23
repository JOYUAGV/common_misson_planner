#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Author: Weihong Liu
Email: liuweihong_cau@163.com
"""

import os
import numpy as np
import pyproj

def parse_wpl_file(file_path):
    with open(file_path, 'r') as file:
        lines = file.readlines()

    waypoints = []
    for line in lines[1:]:  # Skip the first line (header)
        parts = line.strip().split('\t')
        try:
            index = int(parts[0])
            frame = int(parts[1])
            command = int(parts[2])
            param0 = int(float(parts[3]))
            param1 = int(float(parts[4]))
            param2 = int(float(parts[5]))
            param3 = int(float(parts[6]))
            param4 = int(float(parts[7]))
            lat = float(parts[8]) if parts[8] else None
            lon = float(parts[9]) if parts[9] else None
            alt = float(parts[10]) if parts[10] else None
            autocontinue = int(float(parts[11])) if parts[11] else None

            wp = {
                'index': index,
                'frame': frame,
                'command': command,
                'param0': param0, 
                'param1': param1,
                'param2': param2,
                'param3': param3,
                'param4': param4,
                'lat': lat,
                'lon': lon,
                'alt': alt,
                'autocontinue': autocontinue
            }
            waypoints.append(wp)
        except ValueError as e:
            print(f"Error parsing line: {line}\n{e}")
            continue

    return waypoints

def get_utm_zone(lon):
    return int((lon + 180) / 6) + 1

def generate_origin_alignment(waypoints, lon_cur, lat_cur, alt):
    if not waypoints:
        raise ValueError("No waypoints available to process.")
    
    wgs84 = pyproj.Proj(proj='latlong', datum='WGS84')
    
    wp3 = next((wp for wp in waypoints if wp['index'] == 3), None)
    wp4 = next((wp for wp in waypoints if wp['index'] == 4), None)
    
    if wp3 is None or wp4 is None:
        raise ValueError("Cannot find waypoints with index 3 and 4.")
    
    lon1, lat1 = wp3['lon'], wp3['lat']
    
    utm_zone = get_utm_zone(lon1)
    utm = pyproj.Proj(proj='utm', zone=utm_zone, datum='WGS84')
    transformer_to_utm = pyproj.Transformer.from_proj(wgs84, utm)
    transformer_to_latlon = pyproj.Transformer.from_proj(utm, wgs84)

    x_cur, y_cur = transformer_to_utm.transform(lon_cur, lat_cur)
    x_ref, y_ref = transformer_to_utm.transform(lon1, lat1)

    # Calculate offsets
    dx = -(x_ref - x_cur)
    dy = -(y_ref - y_cur)
    print('dx, dy', dx, dy)
    
    origin_alignment = []
    for wp in waypoints:
        lat, lon = wp['lat'], wp['lon']
        if lat is not None and lon is not None and lat != 0 and lon != 0:
            x, y = transformer_to_utm.transform(lon, lat)
            
            # Apply offsets
            x_offset = x + dx
            y_offset = y + dy
            
            # Convert back to latitude/longitude
            lon_new, lat_new = transformer_to_latlon.transform(x_offset, y_offset)
            
            new_wp = wp.copy()
            new_wp['lat'] = lat_new
            new_wp['lon'] = lon_new
            new_wp['alt'] = alt  # Set altitude to new value
            origin_alignment.append(new_wp)
        else:
            # Set altitude to new value for points with zero latitude or longitude
            new_wp = wp.copy()
            new_wp['alt'] = alt
            origin_alignment.append(new_wp)
    
    return origin_alignment

def create_wpl_content(waypoints):
    content = ["QGC WPL 110"]
    for wp in waypoints:
        line = (f"{wp['index']}\t"
                f"{wp['frame']}\t"
                f"{wp['command']}\t"
                f"{wp['param0']}\t" 
                f"{wp['param1']}\t"
                f"{wp['param2']}\t"
                f"{wp['param3']}\t"
                f"{wp['param4']}\t"
                f"{wp['lat']:.8f}\t"
                f"{wp['lon']:.8f}\t"
                f"{wp['alt']:.6f}\t"
                f"{wp['autocontinue']}")
        content.append(line)
    return "\n".join(content)

def main(file_path, lon_cur, lat_cur, alt):
    waypoints = parse_wpl_file(file_path)
    if not waypoints:
        print("No valid waypoints found. Exiting.")
        return
    
    origin_alignment = generate_origin_alignment(waypoints, lon_cur, lat_cur, alt)
    new_wpl_content = create_wpl_content(origin_alignment)
    
    new_file_path = os.path.splitext(file_path)[0] + '_origin_alignment.waypoints'
    with open(new_file_path, 'w') as file:
        file.write(new_wpl_content)
    
    print(f"对齐目标点航线已保存到: {new_file_path}")

# Example usage
'''
Function: 给定当前位置（经纬高格式），将指定文件中所有非零位置进行偏移与当前位置对齐，并将结果（经纬高格式）写入指定文件
'''
file_path = './ref1_tmp.waypoints' # specify the target waypoints that u want to align with current position
lat_cur = 39.463492 # current latitude of the veihcle (deg)
lon_cur = 115.8460445 # current longitude of the veihcle (deg)

# file_path = './ref1_tmp_origin_alignment_mirrored_offset_16.waypoints' # specify the target waypoints that u want to align with current position
# lat_cur = 39.4634814 #39.4634678 # current latitude of the veihcle (deg)
# lon_cur = 115.8461225 #115.8460539 # current longitude of the veihcle (deg)

alt = 5.5  # specify the target altitude (m)

main(file_path, lon_cur, lat_cur, alt)
